from celery.schedules import crontab

# Fuso horário padrão
timezone = "America/Sao_Paulo"

# Configurações de concorrência e tarefas
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
task_track_started = True
task_time_limit = 120  # Timeout máximo de 2 minutos por tarefa de scraping

# Agendamento periódico do Celery Beat
beat_schedule = {
    "orchestrate-price-checks-every-minute": {
        "task": "app.infra.queue.tasks.orchestrate_price_checks",
        "schedule": 60.0,  # Executa a cada 60 segundos (1 minuto)
    }
}
