from celery.schedules import crontab

# Fuso horário padrão
timezone = "America/Sao_Paulo"

# Configurações de serialização e concorrência
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
task_track_started = True
task_time_limit = 120  # Timeout máximo de 2 minutos por tarefa

# Agendamento periódico do Celery Beat
# Executa a cada 60 segundos para verificar produtos com intervalos expirados.
# O filtro por check_interval_minutes é feito na query — cada produto é checado
# apenas quando o SEU intervalo individual expirou.
beat_schedule = {
    "orchestrate-price-checks-every-minute": {
        "task": "app.infra.worker.tasks.price_check.orchestrate_price_checks",
        "schedule": 60.0,
    }
}
