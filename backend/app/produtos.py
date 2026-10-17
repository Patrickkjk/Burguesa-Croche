from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.database import conectar

router = APIRouter(prefix="/produtos", tags=["Produtos"])



class ProdutoCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    categoria: str = Field(min_length=1, max_length=100)
    preco: float = Field(ge=0)
    descricao: str = ""
    material: str = ""
    disponivel: bool = True
    publicado: bool = False

    prazo_producao: str = ""
    altura_modelo: str = ""
    busto_modelo: str = ""
    cintura_modelo: str = ""
    quadril_modelo: str = ""
    medidas_peca: str = ""
    informacoes_tamanho: str = ""
    video: str = ""
    cores: list[str] = []
    tamanhos: list[str] = []
    combinacoes_pronta_entrega: list[str] = []
    cuidados: str = ""


class ProdutoAtualizacao(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    categoria: str = Field(min_length=1, max_length=100)
    preco: float = Field(ge=0)
    descricao: str = ""
    material: str = ""
    disponivel: bool = True
    publicado: bool = False

    prazo_producao: str = ""
    altura_modelo: str = ""
    busto_modelo: str = ""
    cintura_modelo: str = ""
    quadril_modelo: str = ""
    medidas_peca: str = ""
    informacoes_tamanho: str = ""
    video: str = ""
    cores: list[str] = []
    tamanhos: list[str] = []
    combinacoes_pronta_entrega: list[str] = []
    cuidados: str = ""


@router.get("/")
def listar_produtos():
    conexao = conectar()

    try:
        produtos = conexao.execute(
            "SELECT * FROM produtos ORDER BY id DESC"
        ).fetchall()

        return [dict(produto) for produto in produtos]

    finally:
        conexao.close()


@router.get("/{produto_id}")
def buscar_produto(produto_id: int):
    conexao = conectar()

    try:
        produto = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()

        if produto is None:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado",
            )

        return dict(produto)

    finally:
        conexao.close()


@router.post("/", status_code=201)
def cadastrar_produto(produto: ProdutoCriacao):
    conexao = conectar()

    try:
        
       
        cursor = conexao.execute(
            """
            INSERT INTO produtos (
                nome, categoria, preco, descricao, material,
                disponivel, publicado, prazo_producao,
                altura_modelo, busto_modelo, cintura_modelo,
                quadril_modelo, medidas_peca,
                informacoes_tamanho, video,
                cores, tamanhos, combinacoes_pronta_entrega, cuidados
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?)
            """,
            (
                produto.nome.strip(),
                produto.categoria.strip(),
                produto.preco,
                produto.descricao,
                produto.material,
                int(produto.disponivel),
                int(produto.publicado),
                produto.prazo_producao,
                produto.altura_modelo,
                produto.busto_modelo,
                produto.cintura_modelo,
                produto.quadril_modelo,
                produto.medidas_peca,
                produto.informacoes_tamanho,
                produto.video,
                __import__("json").dumps(produto.cores, ensure_ascii=False),
                __import__("json").dumps(produto.tamanhos, ensure_ascii=False),
                __import__("json").dumps(
                    produto.combinacoes_pronta_entrega,
                    ensure_ascii=False,
                ),
                produto.cuidados,
            ),
        )


        conexao.commit()

        novo_produto = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return dict(novo_produto)

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


@router.put("/{produto_id}")
def atualizar_produto(
    produto_id: int,
    produto: ProdutoAtualizacao,
):
    conexao = conectar()

    try:
        produto_existente = conexao.execute(
            "SELECT id FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()

        if produto_existente is None:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado",
            )

        
        
        conexao.execute(
            """
            UPDATE produtos
            SET nome = ?,
                categoria = ?,
                preco = ?,
                descricao = ?,
                material = ?,
                disponivel = ?,
                publicado = ?,
                prazo_producao = ?,
                altura_modelo = ?,
                busto_modelo = ?,
                cintura_modelo = ?,
                quadril_modelo = ?,
                medidas_peca = ?,
                informacoes_tamanho = ?,
                video = ?,
                cores = ?,
                tamanhos = ?,
                combinacoes_pronta_entrega = ?,
                cuidados = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                produto.nome.strip(),
                produto.categoria.strip(),
                produto.preco,
                produto.descricao,
                produto.material,
                int(produto.disponivel),
                int(produto.publicado),
                produto.prazo_producao,
                produto.altura_modelo,
                produto.busto_modelo,
                produto.cintura_modelo,
                produto.quadril_modelo,
                produto.medidas_peca,
                produto.informacoes_tamanho,
                produto.video,
                __import__("json").dumps(produto.cores, ensure_ascii=False),
                __import__("json").dumps(produto.tamanhos, ensure_ascii=False),
                __import__("json").dumps(
                    produto.combinacoes_pronta_entrega,
                    ensure_ascii=False,
                ),
                produto.cuidados,
                produto_id,
            ),
        )

        conexao.commit()

        produto_atualizado = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()

        return dict(produto_atualizado)

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


@router.delete("/{produto_id}")
def excluir_produto(produto_id: int):
    conexao = conectar()

    try:
        produto_existente = conexao.execute(
            "SELECT id FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()

        if produto_existente is None:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado",
            )

        conexao.execute(
            "DELETE FROM produtos WHERE id = ?",
            (produto_id,),
        )

        conexao.commit()

        return {
            "mensagem": "Produto excluído com sucesso",
            "id": produto_id,
        }

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()