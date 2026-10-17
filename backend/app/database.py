
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "burguesa_croche.db"


def conectar():
    conexao = sqlite3.connect(DATABASE_PATH)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    conexao = conectar()

    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT NOT NULL,
                preco REAL NOT NULL CHECK (preco >= 0),
                descricao TEXT DEFAULT '',
                material TEXT DEFAULT '',
                prazo_producao TEXT DEFAULT '',
                condicoes_entrega TEXT DEFAULT '',
                altura_modelo TEXT DEFAULT '',
                busto_modelo TEXT DEFAULT '',
                cintura_modelo TEXT DEFAULT '',
                quadril_modelo TEXT DEFAULT '',
                medidas_peca TEXT DEFAULT '',
                informacoes_tamanho TEXT DEFAULT '',
                disponivel INTEGER NOT NULL DEFAULT 1
                    CHECK (disponivel IN (0, 1)),
                publicado INTEGER NOT NULL DEFAULT 0
                    CHECK (publicado IN (0, 1)),
                video TEXT DEFAULT '',
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS imagens_produto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                caminho TEXT NOT NULL,
                ordem INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (produto_id)
                    REFERENCES produtos(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS variantes_produto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK (tipo IN ('cor', 'tamanho')),
                valor TEXT NOT NULL,
                FOREIGN KEY (produto_id)
                    REFERENCES produtos(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS favoritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                identificador_cliente TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (produto_id, identificador_cliente),
                FOREIGN KEY (produto_id)
                    REFERENCES produtos(id) ON DELETE CASCADE
            );
        """)
        colunas = {
            coluna["name"]
            for coluna in conexao.execute(
                "PRAGMA table_info(produtos)"
            ).fetchall()
        }

        novas_colunas = {
            "cores": "TEXT NOT NULL DEFAULT '[]'",
            "tamanhos": "TEXT NOT NULL DEFAULT '[]'",
            "combinacoes_pronta_entrega": "TEXT NOT NULL DEFAULT '[]'",
            "cuidados": "TEXT NOT NULL DEFAULT ''",
        }

        for nome, definicao in novas_colunas.items():
            if nome not in colunas:
                conexao.execute(
                    f"ALTER TABLE produtos ADD COLUMN {nome} {definicao}"
                )
        conexao.commit()
    finally:
        conexao.close()
