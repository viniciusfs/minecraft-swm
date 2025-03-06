import os
import yaml
import json
import subprocess
import time
import nbt.nbt as nbt

from datetime import datetime, timedelta
from flask import Flask, render_template


DOCKER_COMPOSE_FILE = os.environ['DOCKER_COMPOSE_FILE']
WORLDS_DIR = os.environ['WORLDS_DIR']
CONTAINER_NAME = 'minecraft'

app = Flask(__name__)
app.secret_key = "minecraft_manager_secret_key"


# ROUTES

@app.route('/')
def index():
    server_status = get_server_status()

    worlds = []
    for world in get_world_list():
        worlds.append(get_world_details(world))

    return render_template('index.html', worlds=worlds, server_status=server_status)


@app.route('/world/<world>')
def world_details(world):
    details = get_world_details(world)

    return render_template('world_details.html', world=details)

# COMPOSE FUNCTIONS

def get_active_world():
    try:
        with open(DOCKER_COMPOSE_FILE, 'r') as file:
            compose_data = yaml.safe_load(file)

            env = compose_data['services'][CONTAINER_NAME]['environment']
            if 'LEVEL' in env.keys():
                return env.get('LEVEL')

    except Exception as e:
        print(f"Erro ao ler docker-compose.yml: {e}")

    return None


def update_docker_compose(world_name):
    try:
        with open(DOCKER_COMPOSE_FILE, 'r') as file:
            compose_data = yaml.safe_load(file)

            current_env = compose_data['services'][CONTAINER_NAME]['environment']
            new_env = {'LEVEL': world_name}
            merged_env = current_env.copy()
            merged_env.update(new_env)

            compose_data['services'][CONTAINER_NAME]['environment'] = merged_env

        with open(DOCKER_COMPOSE_FILE, 'w') as file:
            yaml.dump(compose_data, file, sort_keys=False)

        return True

    except Exception as e:
        print(f"Erro ao atualizar docker-compose.yml: {e}")

        return False


def stop_server():
    try:
        compose_dir = os.path.dirname(DOCKER_COMPOSE_FILE)
        os.chdir(compose_dir)
        subprocess.run(["docker-compose", "stop", CONTAINER_NAME], check=True)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao reiniciar o servidor: {e}")

        return False


def start_server():
    try:
        compose_dir = os.path.dirname(DOCKER_COMPOSE_FILE)
        os.chdir(compose_dir)
        subprocess.run(["docker-compose", "up", "-d", CONTAINER_NAME], check=True)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao reiniciar o servidor: {e}")


def get_server_status():
    try:
        compose_dir = os.path.dirname(DOCKER_COMPOSE_FILE)
        os.chdir(compose_dir)

        result = subprocess.run(
            ["docker-compose", "ps", "-q", CONTAINER_NAME],
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
        print(f"Erro ao verificar status do servidor: {e}")
        return {"status": "error", "message": str(e)}

# WORLD READER FUNCTIONS

GAME_MODES = {
    0: "Survival",
    1: "Creative",
    2: "Adventure",
    3: "Spectator"
}

DIFFICULTIES = {
    0: "Peaceful",
    1: "Easy",
    2: "Normal",
    3: "Hard"
}


def get_world_list():
    if not os.path.exists(WORLDS_DIR):
        return []

    worlds = []
    for item in os.listdir(WORLDS_DIR):
        world_path = os.path.join(WORLDS_DIR, item)
        if os.path.isdir(world_path) and "level.dat" in os.listdir(world_path):
            worlds.append(item)

    return worlds


def get_world_details(world_name):
    world_details = {}

    world_path = os.path.join(WORLDS_DIR, world_name)
    level_dat_path = os.path.join(world_path, "level.dat")

    has_level_dat = os.path.exists(level_dat_path)
    has_region_folder = os.path.exists(os.path.join(world_path, "region"))
    has_player_data = os.path.exists(os.path.join(world_path, "playerdata"))
    has_data_folder = os.path.exists(os.path.join(world_path, "data"))

    # get level info
    if has_level_dat:
        nbt_file = nbt.NBTFile(level_dat_path, 'rb')
        data = nbt_file["Data"]

        nbt_data = {
            "name": data['LevelName'].valuestr(),
            "seed": data['WorldGenSettings']['seed'].valuestr(),
            "game_type": data['GameType'].valuestr(),
            "difficulty": data['Difficulty'].valuestr(),
            "version_name": data['Version']['Name'].valuestr(),
            "was_modded": data['WasModded'].valuestr(),
            "allow_commands": data['allowCommands'].valuestr(),
            "last_played": data['LastPlayed'].valuestr(),

            "spawn_x": data['SpawnX'].valuestr(),
            "spawn_y": data['SpawnY'].valuestr(),
            "spawn_z": data['SpawnZ'].valuestr(),

            "game_time": data['Time'].valuestr(),
            "day_time": data['DayTime'].valuestr(),
        }

        game_mode = GAME_MODES.get(int(nbt_data["game_type"]), "Unknown")
        difficulty = DIFFICULTIES.get(int(nbt_data["difficulty"]), "Unknown")

        ticks = int(nbt_data["game_time"])
        seconds = ticks / 20
        played_time = str(timedelta(seconds=seconds))

        if int(nbt_data["last_played"]) > 0:
            last_played_date = datetime.fromtimestamp(
                int(nbt_data["last_played"]) / 1000
            )
            last_played_string = last_played_date.strftime("%d/%m/%Y %H:%M:%S")
        else:
            last_played_string = "Never"

        ingame_current_day = (int(nbt_data["day_time"]) // 24000) + 1

        world_details = {
            "name": nbt_data["name"],
            "dir_name": world_name,
            "seed": nbt_data["seed"],
            "game_mode": game_mode,
            "difficulty": difficulty,
            "version": nbt_data["version_name"],
            "was_modded": nbt_data["was_modded"],
            "allow_commands": nbt_data["allow_commands"],

            "last_played": last_played_string,
            "played_time": played_time,

            "ingame_current_day": ingame_current_day,

            "spawn_x": nbt_data["spawn_x"],
            "spawn_y": nbt_data["spawn_y"],
            "spawn_z": nbt_data["spawn_z"],

            "structure": {
                "has_level_dat": has_level_dat,
                "has_region_folder": has_region_folder,
                "has_player_data": has_player_data,
                "has_data_folder": has_data_folder,
            },
        }

    # get players info
    uuids = []
    if has_player_data:
        player_data_dir = os.path.join(world_path, "playerdata")
        for file in os.listdir(player_data_dir):
            if file.endswith(".dat"):
                uuid = file.replace(".dat", "")
                uuids.append(uuid)

        world_details["players"] = {
            "count": len(uuids),
            "uuids": uuids
        }

    # chunk and file stats
    total_size = 0
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(world_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            file_count += 1

    last_modified = os.path.getmtime(world_path)
    creation_time = os.path.getctime(world_path)

    regions = []
    total_chunks = 0
    if has_region_folder:
        region_dir = os.path.join(world_path, "region")
        for file in os.listdir(region_dir):
            if file.endswith(".mca"):
                region_file = os.path.join(region_dir, file)
                region_size = os.path.getsize(region_file)
                estimated_chunks = max(0, (region_size - 8192) // 4096)
                total_chunks += estimated_chunks

                parts = file.split(".")
                if len(parts) >= 3:
                    try:
                        region_x = int(parts[1])
                        region_z = int(parts[2])
                        regions.append({
                            "file": file,
                            "x": region_x,
                            "z": region_z,
                            "size_mb": round(region_size / (1024 * 1024), 2),
                            "estimated_chunks": estimated_chunks
                        })
                    except:
                        pass

        world_details["file_stats"] = {
            "size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "last_modified": time.ctime(last_modified),
            "creation_time": time.ctime(creation_time),
        }

        world_details["regions"] = {
            "count": len(regions),
            "data": regions,
            "total_chunks": total_chunks,
            "estimated_world_size_blocks": total_chunks * 16 * 16
        }

    return world_details


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
