from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request
from app.services.docker_service import get_server_status, start_server, stop_server
from app.services.world_service import get_world_list, get_world_details

bp = Blueprint('main', __name__, template_folder='templates')


@bp.route('/')
def index():
    server_status = get_server_status()

    worlds = []
    for world in get_world_list():
        worlds.append(get_world_details(world))

    return render_template('index.html', worlds=worlds, server_status=server_status)


@bp.route('/restart', methods=['POST'])
def restart_server():
    if stop_server():
        if start_server():
            flash('Servidor reiniciado com sucesso!', 'success')
        else:
            flash('Falha ao iniciar o servidor!', 'error')
    else:
        flash('Falha ao parar o servidor!', 'error')

    return redirect(url_for('main.index'))
