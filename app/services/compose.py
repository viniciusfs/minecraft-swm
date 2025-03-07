import os
import json
import subprocess
import yaml

from flask import current_app


class DoubleQuoteDumper(yaml.Dumper):
    def represent_str(self, data):
        return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')


DoubleQuoteDumper.add_representer(str, DoubleQuoteDumper.represent_str)


def get_active_world():
    try:
        docker_compose_file = current_app.config['DOCKER_COMPOSE_FILE']
        container_name = current_app.config['CONTAINER_NAME']

        with open(docker_compose_file, 'r') as file:
            compose_data = yaml.safe_load(file)
            env = compose_data['services'][container_name]['environment']
            if 'LEVEL' in env.keys():
                print(env.get('LEVEL'))
                return env.get('LEVEL')

    except Exception as e:
        current_app.logger.error(f"Error reading docker-compose.yml: {e}")

    return None


def update_docker_compose(name):
    try:
        docker_compose_file = current_app.config['DOCKER_COMPOSE_FILE']
        container_name = current_app.config['CONTAINER_NAME']
        prefix = os.path.basename(current_app.config['WORLDS_DIR'])
        world_name = prefix + "/" + name

        with open(docker_compose_file, 'r') as file:
            compose_data = yaml.safe_load(file)

            current_env = compose_data['services'][container_name]['environment']
            new_env = {'LEVEL': world_name}
            merged_env = current_env.copy()
            merged_env.update(new_env)

            compose_data['services'][container_name]['environment'] = merged_env

        with open(docker_compose_file, 'w') as file:
            yaml.dump(compose_data, file, sort_keys=False, Dumper=DoubleQuoteDumper)

        return True

    except Exception as e:
        current_app.logger.error(f"Error updating docker-compose.yml: {e}")
        return False


def stop_server():
    try:
        docker_compose_file = current_app.config['DOCKER_COMPOSE_FILE']
        container_name = current_app.config['CONTAINER_NAME']

        compose_dir = os.path.dirname(docker_compose_file)
        os.chdir(compose_dir)
        subprocess.run(["docker", "compose", "stop", container_name], check=True)

        return True

    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Error stopping the server: {e}")
        return False


def start_server():
    try:
        docker_compose_file = current_app.config['DOCKER_COMPOSE_FILE']
        container_name = current_app.config['CONTAINER_NAME']

        compose_dir = os.path.dirname(docker_compose_file)
        os.chdir(compose_dir)
        subprocess.run(["docker", "compose", "up", "-d", container_name], check=True)

        return True

    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Error starting the server: {e}")
        return False


def get_server_status():
    try:
        docker_compose_file = current_app.config['DOCKER_COMPOSE_FILE']
        container_name = current_app.config['CONTAINER_NAME']

        compose_dir = os.path.dirname(docker_compose_file)
        os.chdir(compose_dir)

        result = subprocess.run(
            ["docker", "compose", "ps", "-q", container_name],
            check=True,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            stats = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "json", result.stdout.strip()],
                check=True,
                capture_output=True,
                text=True
            )

            if stats.stdout:
                container_stats = json.loads(stats.stdout)
                return {
                    "status": "running",
                    "cpu": container_stats.get("CPUPerc", "N/A"),
                    "memory": container_stats.get("MemUsage", "N/A"),
                    "container_id": result.stdout.strip()
                }
            return {"status": "running", "container_id": result.stdout.strip()}

        else:
            return {"status": "stopped"}

    except Exception as e:
        current_app.logger.error(f"Error checking server status: {e}")
        return {"status": "error", "message": str(e)}
