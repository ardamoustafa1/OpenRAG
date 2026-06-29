# Backup & Recovery Procedures

## Velero Backups

The AI Platform relies on [Velero](https://velero.io/) to securely back up all stateful volumes (PostgreSQL, Qdrant, MinIO) to an S3-compatible remote storage bucket.

### Daily Snapshot Schedule
A daily backup is scheduled at 2:00 AM via `velero-schedule.yaml`. It snapshots all PVCs in the `ai-platform` namespace and retains them for 30 days.

### Triggering a Manual Backup
Before any major upgrade, manually trigger a backup:
```bash
velero backup create pre-upgrade-backup --include-namespaces ai-platform --wait
```

### Restoring from a Backup
In the event of complete namespace loss or severe data corruption:
```bash
velero restore create --from-backup pre-upgrade-backup --wait
```

## PostgreSQL Point-in-Time Recovery (PITR)
For finer granularity than daily snapshots, the `postgresql` subchart is configured with WAL archiving.
WAL archives are continuously shipped to MinIO. If a tenant accidentally deletes critical data at 14:35, you can restore the database state to exactly 14:34 using `pgBackRest` or standard WAL replay mechanisms.
