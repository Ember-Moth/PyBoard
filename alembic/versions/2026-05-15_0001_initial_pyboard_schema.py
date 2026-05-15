"""initial pyboard schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15 06:00:00.000000
"""

import os
import sys
from typing import Sequence, Union

from alembic import context, op

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.migrations.seeds import seed_default_settings_sync, seed_initial_admin_sync


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIMESTAMP_TABLES: tuple[str, ...] = (
    "commission_log",
    "coupon",
    "failed_jobs",
    "giftcard",
    "giftcard_redemption",
    "invite_code",
    "knowledge",
    "log_event",
    "notice",
    "orders",
    "payment",
    "plan",
    "queue_job",
    "runtime_cache",
    "server_group",
    "server_route",
    "server_v2node",
    "setting",
    "stat",
    "stat_server",
    "stat_user",
    "ticket",
    "ticket_message",
    "traffic_cache",
    "users",
)


def upgrade() -> None:
    _create_tables()
    _create_indexes()
    _create_timestamp_function()
    _apply_timestamp_triggers()
    _create_enqueue_function()
    _create_runtime_cleanup_function()
    _ensure_pg_cron_extension()
    _create_cron_functions()
    op.execute("SELECT pyboard_schedule_pg_cron_jobs()")
    if not context.is_offline_mode():
        connection = op.get_bind()
        seed_default_settings_sync(connection)
        seed_initial_admin_sync(connection)


def downgrade() -> None:
    op.execute("SELECT pyboard_unschedule_pg_cron_jobs()")
    op.execute("DROP FUNCTION IF EXISTS pyboard_unschedule_pg_cron_jobs()")
    op.execute("DROP FUNCTION IF EXISTS pyboard_schedule_pg_cron_jobs()")
    op.execute("DROP FUNCTION IF EXISTS pyboard_enqueue_queue_job(text, jsonb, jsonb, text, text, bigint)")
    op.execute("DROP FUNCTION IF EXISTS pyboard_cleanup_runtime_cache()")
    for table in reversed(TIMESTAMP_TABLES):
        op.execute(f'DROP TRIGGER IF EXISTS "trg_{table}_timestamps" ON "{table}"')
    op.execute("DROP FUNCTION IF EXISTS pyboard_set_epoch_timestamps()")
    for table in reversed(TIMESTAMP_TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{table}"')


def _create_tables() -> None:
    _execute_statements(
        f"""
        CREATE TABLE commission_log (
            invite_user_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            trade_no VARCHAR(36) NOT NULL,
            order_amount INTEGER NOT NULL,
            get_amount INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_commission_log_trade_no UNIQUE (trade_no)
        );

        CREATE TABLE coupon (
            code VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            type INTEGER NOT NULL,
            value INTEGER NOT NULL,
            show BOOLEAN NOT NULL,
            limit_use INTEGER,
            limit_use_with_user INTEGER,
            limit_plan_ids VARCHAR(255),
            limit_period VARCHAR(255),
            started_at INTEGER NOT NULL,
            ended_at INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE failed_jobs (
            connection VARCHAR NOT NULL,
            queue VARCHAR NOT NULL,
            payload JSONB DEFAULT '{{}}'::jsonb NOT NULL,
            exception VARCHAR NOT NULL,
            failed_at VARCHAR NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE giftcard (
            code VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            type INTEGER NOT NULL,
            value INTEGER,
            plan_id INTEGER,
            limit_use INTEGER,
            used_user_ids VARCHAR(16384),
            started_at INTEGER NOT NULL,
            ended_at INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE giftcard_redemption (
            giftcard_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            code VARCHAR(255) NOT NULL,
            type INTEGER NOT NULL,
            value INTEGER,
            plan_id INTEGER,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_giftcard_redemption_giftcard_user UNIQUE (giftcard_id, user_id)
        );

        CREATE TABLE invite_code (
            user_id INTEGER NOT NULL,
            code VARCHAR(32) NOT NULL,
            status INTEGER NOT NULL,
            pv INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE knowledge (
            language VARCHAR(5) NOT NULL,
            category VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            body VARCHAR NOT NULL,
            sort INTEGER,
            show BOOLEAN NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE log_event (
            level VARCHAR(16) NOT NULL,
            category VARCHAR(32) NOT NULL,
            event VARCHAR(64) NOT NULL,
            message VARCHAR(255) NOT NULL,
            request_id VARCHAR(64),
            trace_id VARCHAR(64),
            actor_type VARCHAR(32),
            actor_id INTEGER,
            target_type VARCHAR(32),
            target_id VARCHAR(64),
            method VARCHAR(11),
            path VARCHAR(255),
            status_code INTEGER,
            duration_ms INTEGER,
            ip VARCHAR(128),
            user_agent VARCHAR(255),
            data JSONB,
            error_type VARCHAR(128),
            error_stack TEXT,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE notice (
            title VARCHAR(255) NOT NULL,
            content VARCHAR NOT NULL,
            show BOOLEAN NOT NULL,
            img_url VARCHAR(255),
            tags VARCHAR(255),
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE orders (
            invite_user_id INTEGER,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            coupon_id INTEGER,
            payment_id INTEGER,
            type INTEGER NOT NULL,
            period VARCHAR(255) NOT NULL,
            trade_no VARCHAR(36) NOT NULL,
            callback_no VARCHAR(255),
            total_amount INTEGER NOT NULL,
            handling_amount INTEGER,
            discount_amount INTEGER,
            surplus_amount INTEGER,
            refund_amount INTEGER,
            balance_amount INTEGER,
            surplus_order_ids VARCHAR,
            status INTEGER NOT NULL,
            commission_status INTEGER NOT NULL,
            commission_balance INTEGER NOT NULL,
            actual_commission_balance INTEGER,
            paid_at INTEGER,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_orders_trade_no UNIQUE (trade_no)
        );

        CREATE TABLE payment (
            uuid VARCHAR(32) NOT NULL,
            payment VARCHAR(16) NOT NULL,
            name VARCHAR(255) NOT NULL,
            icon VARCHAR(255),
            config JSONB DEFAULT '{{}}'::jsonb NOT NULL,
            notify_domain VARCHAR(128),
            handling_fee_fixed INTEGER,
            handling_fee_percent FLOAT,
            enable BOOLEAN NOT NULL,
            sort INTEGER,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE plan (
            group_id INTEGER NOT NULL,
            transfer_enable BIGINT NOT NULL,
            device_limit INTEGER,
            name VARCHAR(255) NOT NULL,
            speed_limit INTEGER,
            show BOOLEAN NOT NULL,
            sort INTEGER,
            renew BOOLEAN NOT NULL,
            content VARCHAR,
            month_price INTEGER,
            quarter_price INTEGER,
            half_year_price INTEGER,
            year_price INTEGER,
            two_year_price INTEGER,
            three_year_price INTEGER,
            onetime_price INTEGER,
            reset_price INTEGER,
            reset_traffic_method INTEGER,
            capacity_limit INTEGER,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE queue_job (
            queue VARCHAR(64) NOT NULL,
            job_name VARCHAR(128) NOT NULL,
            job_key VARCHAR(255),
            args JSONB DEFAULT '[]'::jsonb NOT NULL,
            kwargs JSONB DEFAULT '{{}}'::jsonb NOT NULL,
            status VARCHAR(16) NOT NULL,
            attempts INTEGER NOT NULL,
            max_tries INTEGER NOT NULL,
            scheduled_at BIGINT NOT NULL,
            reserved_at BIGINT,
            finished_at BIGINT,
            failed_at BIGINT,
            last_error VARCHAR,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_queue_job_job_key UNIQUE (job_key)
        );

        CREATE UNLOGGED TABLE runtime_cache (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            expires_at BIGINT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL
        );

        CREATE TABLE server_group (
            name VARCHAR(255) NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE server_route (
            remarks VARCHAR(255) NOT NULL,
            match JSONB NOT NULL,
            action VARCHAR(11) NOT NULL,
            action_value JSONB,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE server_v2node (
            group_id JSONB NOT NULL,
            route_id JSONB,
            name VARCHAR(255) NOT NULL,
            parent_id INTEGER,
            host VARCHAR(255) NOT NULL,
            listen_ip VARCHAR(255) NOT NULL,
            port VARCHAR(11) NOT NULL,
            server_port INTEGER NOT NULL,
            tags JSONB,
            rate VARCHAR(11) NOT NULL,
            show BOOLEAN NOT NULL,
            sort INTEGER,
            protocol VARCHAR(24) NOT NULL,
            tls INTEGER NOT NULL,
            tls_settings JSONB,
            flow VARCHAR(64),
            network VARCHAR(11) NOT NULL,
            network_settings JSONB,
            encryption VARCHAR(64),
            encryption_settings JSONB,
            disable_sni BOOLEAN NOT NULL,
            udp_relay_mode VARCHAR(64),
            zero_rtt_handshake BOOLEAN NOT NULL,
            congestion_control VARCHAR(64),
            cipher VARCHAR(64),
            up_mbps INTEGER NOT NULL,
            down_mbps INTEGER NOT NULL,
            obfs VARCHAR(64),
            obfs_password VARCHAR(255),
            padding_scheme JSONB,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE setting (
            key VARCHAR(64) NOT NULL,
            value TEXT NOT NULL,
            type VARCHAR(8) NOT NULL,
            description VARCHAR(255),
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_setting_key UNIQUE (key)
        );

        CREATE TABLE stat (
            record_at INTEGER NOT NULL,
            record_type VARCHAR(1) NOT NULL,
            order_count INTEGER NOT NULL,
            order_total INTEGER NOT NULL,
            commission_count INTEGER NOT NULL,
            commission_total INTEGER NOT NULL,
            paid_count INTEGER NOT NULL,
            paid_total INTEGER NOT NULL,
            register_count INTEGER NOT NULL,
            invite_count INTEGER NOT NULL,
            transfer_used_total VARCHAR(32) NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_stat_record_at UNIQUE (record_at)
        );

        CREATE TABLE stat_server (
            server_id INTEGER NOT NULL,
            server_type VARCHAR(11) NOT NULL,
            u BIGINT NOT NULL,
            d BIGINT NOT NULL,
            record_type VARCHAR(1) NOT NULL,
            record_at INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE stat_user (
            user_id INTEGER NOT NULL,
            server_rate FLOAT NOT NULL,
            u BIGINT NOT NULL,
            d BIGINT NOT NULL,
            record_type VARCHAR(2) NOT NULL,
            record_at INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE ticket (
            user_id INTEGER NOT NULL,
            subject VARCHAR(255) NOT NULL,
            level INTEGER NOT NULL,
            status INTEGER NOT NULL,
            reply_status INTEGER NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE TABLE ticket_message (
            user_id INTEGER NOT NULL,
            ticket_id INTEGER NOT NULL,
            message VARCHAR NOT NULL,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id)
        );

        CREATE UNLOGGED TABLE traffic_cache (
            stage TEXT NOT NULL,
            user_id BIGINT NOT NULL,
            u BIGINT NOT NULL DEFAULT 0,
            d BIGINT NOT NULL DEFAULT 0,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (stage, user_id)
        );

        CREATE TABLE users (
            email VARCHAR(64) NOT NULL,
            password VARCHAR(255) NOT NULL,
            token VARCHAR(32) NOT NULL,
            invite_user_id INTEGER,
            telegram_id INTEGER,
            balance INTEGER NOT NULL,
            discount INTEGER,
            commission_type INTEGER NOT NULL,
            commission_rate INTEGER,
            commission_balance INTEGER NOT NULL,
            t BIGINT NOT NULL,
            u BIGINT NOT NULL,
            d BIGINT NOT NULL,
            transfer_enable BIGINT NOT NULL,
            group_id INTEGER,
            plan_id INTEGER,
            speed_limit INTEGER,
            device_limit INTEGER,
            banned BOOLEAN NOT NULL,
            is_admin BOOLEAN NOT NULL,
            is_staff BOOLEAN NOT NULL,
            auto_renewal INTEGER NOT NULL,
            remind_expire INTEGER NOT NULL,
            remind_traffic INTEGER NOT NULL,
            last_login_at INTEGER,
            last_login_ip INTEGER,
            uuid VARCHAR(36) NOT NULL,
            expired_at BIGINT NOT NULL,
            remarks VARCHAR,
            id SERIAL NOT NULL,
            created_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            updated_at BIGINT DEFAULT {_epoch_now()} NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_users_email UNIQUE (email),
            CONSTRAINT uq_users_token UNIQUE (token)
        );
        """
    )


def _create_indexes() -> None:
    statements = (
        "CREATE INDEX ix_giftcard_redemption_giftcard_id ON giftcard_redemption (giftcard_id)",
        "CREATE INDEX ix_giftcard_redemption_user_id ON giftcard_redemption (user_id)",
        "CREATE INDEX ix_log_event_actor_id ON log_event (actor_id)",
        "CREATE INDEX ix_log_event_category ON log_event (category)",
        "CREATE INDEX ix_log_event_created_at ON log_event (created_at)",
        "CREATE INDEX ix_log_event_event ON log_event (event)",
        "CREATE INDEX ix_log_event_level ON log_event (level)",
        "CREATE INDEX ix_log_event_request_id ON log_event (request_id)",
        "CREATE INDEX ix_log_event_category_created_at ON log_event (category, created_at)",
        "CREATE INDEX ix_log_event_target ON log_event (target_type, target_id)",
        "CREATE INDEX ix_orders_user_id ON orders (user_id)",
        "CREATE INDEX ix_queue_job_failed_at ON queue_job (failed_at)",
        "CREATE INDEX ix_queue_job_finished_at ON queue_job (finished_at)",
        "CREATE INDEX ix_queue_job_job_name ON queue_job (job_name)",
        "CREATE INDEX ix_queue_job_queue ON queue_job (queue)",
        "CREATE INDEX ix_queue_job_reserved_at ON queue_job (reserved_at)",
        "CREATE INDEX ix_queue_job_scheduled_at ON queue_job (scheduled_at)",
        "CREATE INDEX ix_queue_job_status ON queue_job (status)",
        "CREATE INDEX ix_runtime_cache_expires_at ON runtime_cache (expires_at)",
        "CREATE INDEX ix_stat_server_record_at ON stat_server (record_at)",
        "CREATE INDEX ix_stat_server_server_id ON stat_server (server_id)",
        "CREATE INDEX ix_stat_user_record_at ON stat_user (record_at)",
        "CREATE INDEX ix_stat_user_user_id ON stat_user (user_id)",
        "CREATE INDEX ix_traffic_cache_stage ON traffic_cache (stage)",
    )
    for statement in statements:
        op.execute(statement)


def _create_timestamp_function() -> None:
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION pyboard_set_epoch_timestamps()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            epoch_now BIGINT := {_epoch_now()};
        BEGIN
            IF TG_OP = 'INSERT' THEN
                NEW.created_at := COALESCE(NULLIF(NEW.created_at, 0), epoch_now);
                NEW.updated_at := COALESCE(NULLIF(NEW.updated_at, 0), NEW.created_at);
            ELSE
                NEW.updated_at := epoch_now;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )


def _apply_timestamp_triggers() -> None:
    for table in TIMESTAMP_TABLES:
        op.execute(
            f"""
            CREATE TRIGGER "trg_{table}_timestamps"
            BEFORE INSERT OR UPDATE ON "{table}"
            FOR EACH ROW EXECUTE FUNCTION pyboard_set_epoch_timestamps()
            """
        )


def _create_enqueue_function() -> None:
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION pyboard_enqueue_queue_job(
            p_job_name TEXT,
            p_args JSONB DEFAULT '[]'::jsonb,
            p_kwargs JSONB DEFAULT '{{}}'::jsonb,
            p_queue TEXT DEFAULT 'default',
            p_job_key TEXT DEFAULT NULL,
            p_scheduled_at BIGINT DEFAULT NULL
        )
        RETURNS BIGINT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            new_id BIGINT;
        BEGIN
            INSERT INTO queue_job(queue, job_name, job_key, args, kwargs, status, attempts, max_tries, scheduled_at)
            VALUES (
                p_queue,
                p_job_name,
                p_job_key,
                COALESCE(p_args, '[]'::jsonb),
                COALESCE(p_kwargs, '{{}}'::jsonb),
                'pending',
                0,
                3,
                COALESCE(p_scheduled_at, {_epoch_now()})
            )
            ON CONFLICT (job_key) DO NOTHING
            RETURNING id INTO new_id;
            RETURN new_id;
        END;
        $$;
        """
    )


def _create_runtime_cleanup_function() -> None:
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION pyboard_cleanup_runtime_cache()
        RETURNS INTEGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM runtime_cache
            WHERE expires_at IS NOT NULL
              AND expires_at <= {_epoch_now()};
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$;
        """
    )


def _ensure_pg_cron_extension() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                CREATE EXTENSION IF NOT EXISTS pg_cron;
            EXCEPTION
                WHEN others THEN
                    RAISE NOTICE 'pg_cron is not available for this database or current role; skipping cron schedule bootstrap: %', SQLERRM;
            END;
        END
        $$;
        """
    )


def _create_cron_functions() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION pyboard_unschedule_pg_cron_jobs()
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        DECLARE
            job TEXT;
        BEGIN
            IF to_regnamespace('cron') IS NULL THEN
                RETURN;
            END IF;
            FOREACH job IN ARRAY ARRAY[
                'pyboard_traffic_update_every_minute',
                'pyboard_check_order_every_5_minutes',
                'pyboard_aggregate_yesterday_stats',
                'pyboard_runtime_cache_cleanup',
                'pyboard_cleanup_log_events_daily'
            ]
            LOOP
                BEGIN
                    PERFORM cron.unschedule(job);
                EXCEPTION WHEN others THEN
                    NULL;
                END;
            END LOOP;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION pyboard_schedule_pg_cron_jobs()
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF to_regnamespace('cron') IS NULL THEN
                RETURN;
            END IF;
            PERFORM pyboard_unschedule_pg_cron_jobs();
            BEGIN
                PERFORM cron.schedule(
                    'pyboard_traffic_update_every_minute',
                    '* * * * *',
                    $cron$SELECT pyboard_enqueue_queue_job('traffic_update', '[]'::jsonb, '{}'::jsonb, 'default', 'cron:traffic_update:' || floor(extract(epoch from date_trunc('minute', now())))::text)$cron$
                );
                PERFORM cron.schedule(
                    'pyboard_check_order_every_5_minutes',
                    '*/5 * * * *',
                    $cron$SELECT pyboard_enqueue_queue_job('check_order', '[]'::jsonb, '{}'::jsonb, 'default', 'cron:check_order:' || floor(extract(epoch from date_trunc('minute', now())))::text)$cron$
                );
                PERFORM cron.schedule(
                    'pyboard_aggregate_yesterday_stats',
                    '5 0 * * *',
                    $cron$SELECT pyboard_enqueue_queue_job('aggregate_yesterday_stats', '[]'::jsonb, '{}'::jsonb, 'default', 'cron:aggregate_yesterday_stats:' || to_char(now(), 'YYYYMMDD'))$cron$
                );
                PERFORM cron.schedule(
                    'pyboard_runtime_cache_cleanup',
                    '*/10 * * * *',
                    $cron$SELECT pyboard_cleanup_runtime_cache()$cron$
                );
                PERFORM cron.schedule(
                    'pyboard_cleanup_log_events_daily',
                    '25 3 * * *',
                    $cron$SELECT pyboard_enqueue_queue_job('cleanup_log_events', '[]'::jsonb, '{}'::jsonb, 'default', 'cron:cleanup_log_events:' || to_char(now(), 'YYYYMMDD'))$cron$
                );
            EXCEPTION WHEN undefined_function THEN
                RAISE NOTICE 'pg_cron functions are not available; skipping cron schedule bootstrap';
            END;
        END;
        $$;
        """
    )


def _epoch_now() -> str:
    return "(floor(extract(epoch from now())))::bigint"


def _execute_statements(sql: str) -> None:
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            op.execute(statement)
