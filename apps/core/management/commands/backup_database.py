import os
import gzip
import shutil
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.core.utils import log_audit


class Command(BaseCommand):
    help = "Create an automated, compressed backup of the QMS database (ISO 9001:2015 Clause 7.5.3 compliant)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--prune-days',
            type=int,
            default=30,
            help='Automatically delete backups older than N days (default: 30)'
        )
        parser.add_argument(
            '--no-compress',
            action='store_true',
            help='Do not compress the backup with gzip'
        )

    def handle(self, *args, **options):
        prune_days = options.get('prune_days', 30)
        compress = not options.get('no_compress', False)

        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)

        db_config = settings.DATABASES['default']
        engine = db_config['ENGINE']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.stdout.write(self.style.NOTICE(f"Initiating QMS database backup [{engine}]..."))

        backup_filename = None
        final_path = None

        if 'sqlite3' in engine:
            raw_backup_name = f"qms_sqlite_{timestamp}.db"
            raw_path = backup_dir / raw_backup_name

            # Use sqlite3 live backup API directly on active connection
            self.stdout.write("Creating consistent SQLite snapshot via Connection.backup()...")
            try:
                from django.db import connection as django_conn
                django_conn.ensure_connection()
                dst_conn = sqlite3.connect(str(raw_path))
                django_conn.connection.backup(dst_conn, pages=100)
                dst_conn.close()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"SQLite backup failed: {e}"))
                return

            if compress:
                final_filename = f"{raw_backup_name}.gz"
                final_path = backup_dir / final_filename
                with open(raw_path, 'rb') as f_in, gzip.open(final_path, 'wb', compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)
                if raw_path.exists():
                    raw_path.unlink()
                backup_filename = final_filename
            else:
                backup_filename = raw_backup_name
                final_path = raw_path

        elif 'postgresql' in engine:
            # PostgreSQL database backup
            db_name = db_config.get('NAME')
            user = db_config.get('USER', '')
            host = db_config.get('HOST', 'localhost')
            port = str(db_config.get('PORT', '5432'))
            password = db_config.get('PASSWORD', '')

            pg_dump_bin = shutil.which('pg_dump')

            if pg_dump_bin:
                raw_filename = f"qms_pg_{timestamp}.sql"
                raw_path = backup_dir / raw_filename
                env = os.environ.copy()
                if password:
                    env['PGPASSWORD'] = password

                import subprocess
                cmd = [
                    pg_dump_bin,
                    '-h', host,
                    '-p', port,
                    '-U', user,
                    '-F', 'p',  # plain SQL
                    '-d', db_name,
                    '-f', str(raw_path)
                ]
                self.stdout.write(f"Running pg_dump for database {db_name}...")
                res = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if res.returncode != 0:
                    self.stderr.write(self.style.ERROR(f"pg_dump error: {res.stderr}"))
                    return

                if compress:
                    final_filename = f"{raw_filename}.gz"
                    final_path = backup_dir / final_filename
                    with open(raw_path, 'rb') as f_in, gzip.open(final_path, 'wb', compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    if raw_path.exists():
                        raw_path.unlink()
                    backup_filename = final_filename
                else:
                    backup_filename = raw_filename
                    final_path = raw_path
            else:
                # Fallback to Django dumpdata if pg_dump is not in PATH
                self.stdout.write("pg_dump binary not found in PATH; falling back to Django dumpdata JSON stream...")
                from django.core import management
                raw_filename = f"qms_dumpdata_{timestamp}.json"
                raw_path = backup_dir / raw_filename
                with open(raw_path, 'w', encoding='utf-8') as f:
                    management.call_command(
                        'dumpdata',
                        exclude=['contenttypes', 'auth.permission'],
                        stdout=f,
                        indent=2
                    )

                if compress:
                    final_filename = f"{raw_filename}.gz"
                    final_path = backup_dir / final_filename
                    with open(raw_path, 'rb') as f_in, gzip.open(final_path, 'wb', compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    if raw_path.exists():
                        raw_path.unlink()
                    backup_filename = final_filename
                else:
                    backup_filename = raw_filename
                    final_path = raw_path

        else:
            self.stderr.write(self.style.ERROR(f"Unsupported database engine for direct backup: {engine}"))
            return

        # Compute SHA-256 checksum for audit and integrity verification
        sha256 = hashlib.sha256()
        with open(final_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        checksum = sha256.hexdigest()

        file_size_bytes = final_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        # Audit log entry
        log_audit(
            user=None,
            action='BACKUP',
            module='System',
            record_id=backup_filename,
            record_name=f"QMS Database Backup ({backup_filename})",
            notes=f"Engine: {engine} | Size: {file_size_mb:.2f} MB | SHA256: {checksum[:16]}... | Compressed: {compress}"
        )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created backup archive:\n"
            f"  File:     {final_path}\n"
            f"  Size:     {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)\n"
            f"  SHA-256:  {checksum}\n"
        ))

        # Retention auto-pruning
        if prune_days > 0:
            cutoff = datetime.now() - timedelta(days=prune_days)
            pruned_count = 0
            for existing_file in backup_dir.glob('qms_*'):
                if existing_file.is_file():
                    mtime = datetime.fromtimestamp(existing_file.stat().st_mtime)
                    if mtime < cutoff:
                        existing_file.unlink()
                        pruned_count += 1
                        self.stdout.write(self.style.WARNING(f"Pruned expired backup: {existing_file.name}"))

            if pruned_count:
                self.stdout.write(self.style.NOTICE(f"Auto-pruned {pruned_count} backup(s) older than {prune_days} days."))

        return str(final_path)
