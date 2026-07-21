import sys
import subprocess
import time


def run_command(command: str) -> bool:
    """Executa um comando no shell e exibe o output em tempo real."""
    print(f"\n[EXEC] Running: {command}...")
    try:
        # Usa shell=True para compatibilidade entre Windows e Linux
        result = subprocess.run(command, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] O comando falhou com o erro: {e}")
        return False


def start_project():
    """Sobe os containers, compila e aplica as migrações do banco de dados."""
    print("=" * 60)
    print("🚀 INICIALIZANDO A API DE MONITORAMENTO DE PREÇOS")
    print("=" * 60)
    
    # 1. Sobe e compila os containers
    print("\nStep 1: Subindo os containers no Docker...")
    if not run_command("docker-compose up --build -d"):
        print("\n❌ Falha ao iniciar os containers do Docker. Verifique se o Docker Desktop está rodando.")
        return

    # 2. Aguarda um curto período para garantir a inicialização dos bancos
    print("\nStep 2: Aguardando 5 segundos para estabilização do banco...")
    time.sleep(5)

    # 3. Executa as migrações do Alembic
    print("\nStep 3: Aplicando migrações do banco de dados (Alembic)...")
    if not run_command("docker-compose exec web alembic upgrade head"):
        print("\n⚠️ Alerta: Falha ao rodar as migrações do Alembic. O banco de dados pode ainda estar inicializando.")
        print("Você pode tentar executar novamente rodando: python run.py migrate")
    
    # 4. Status
    print("\nStep 4: Verificando status dos containers...")
    run_command("docker ps")

    print("\n" + "=" * 60)
    print("🎉 API Iniciada com sucesso!")
    print("Acesse no navegador:")
    print("  - API Swagger UI: http://localhost:8000/docs")
    print("  - pgAdmin 4:       http://localhost:8080")
    print("  - Selenium Grid:   http://localhost:7900 (Senha: secret)")
    print("=" * 60)


def stop_project():
    """Para todos os containers da aplicação."""
    print("=" * 60)
    print("🛑 PARANDO A API DE MONITORAMENTO DE PREÇOS")
    print("=" * 60)
    run_command("docker-compose down")
    print("\n✅ Todos os containers foram desligados.")


def run_migrations():
    """Apenas aplica as migrações do Alembic."""
    print("\n🔄 Aplicando migrações do Alembic no container...")
    run_command("docker-compose exec web alembic upgrade head")


def show_logs():
    """Acompanha os logs em tempo real."""
    print("\n📋 Exibindo logs (Pressione CTRL+C para sair)...")
    try:
        run_command("docker-compose logs -f")
    except KeyboardInterrupt:
        print("\nSaindo da visualização de logs.")


def show_status():
    """Mostra o status de saúde dos containers."""
    print("\n📊 Status atual dos containers:")
    run_command("docker ps")


def main():
    if len(sys.argv) < 2:
        print("Uso recomendado: python run.py [start | stop | migrate | logs | status]")
        print("Menu interativo:")
        print("  1. Iniciar/Buildar Projeto (Docker + Migrações)")
        print("  2. Parar Containers")
        print("  3. Rodar Migrações do Banco")
        print("  4. Ver Logs em Tempo Real")
        print("  5. Ver Status dos Containers")
        
        try:
            choice = input("\nEscolha uma opção (1-5): ").strip()
            if choice == "1":
                start_project()
            elif choice == "2":
                stop_project()
            elif choice == "3":
                run_migrations()
            elif choice == "4":
                show_logs()
            elif choice == "5":
                show_status()
            else:
                print("Opção inválida.")
        except (KeyboardInterrupt, EOFError):
            print("\nSaindo...")
        return

    action = sys.argv[1].lower()
    if action == "start":
        start_project()
    elif action == "stop":
        stop_project()
    elif action == "migrate":
        run_migrations()
    elif action == "logs":
        show_logs()
    elif action == "status":
        show_status()
    else:
        print(f"Ação desconhecida: '{action}'")
        print("Ações válidas: start, stop, migrate, logs, status")


if __name__ == "__main__":
    main()
