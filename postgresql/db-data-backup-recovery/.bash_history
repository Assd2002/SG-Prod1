ls -l /var/lib/postgresql/18/docker/global/pg_control
psql -d postgres -c '\du'
env | grep -E 'POSTGRES_USER|POSTGRES_DB|PGDATA'
SSSSexit
exit
