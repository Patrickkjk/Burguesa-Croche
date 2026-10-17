
const ProdutosService = (() => {
  const API_URL = CONFIG.apiUrl;

  function listaDeTextos(valor) {
    if (!Array.isArray(valor)) return [];

    return [
      ...new Set(
        valor
          .filter(item => typeof item === "string")
          .map(item => item.trim())
          .filter(Boolean)
      )
    ];
  }

  function midiaValida(valor) {
    return (
      typeof valor === "string" ||
      (typeof Blob !== "undefined" && valor instanceof Blob)
    );
  }

  function normalizarProduto(produto) {
    if (!produto || typeof produto !== "object") {
      throw new Error("Os dados da peça são inválidos.");
    }

    const name = String(produto.name || "").trim();
    const category = String(produto.category || "").trim();

    if (!name) {
      throw new Error("Informe o nome da peça.");
    }

    if (!category || category === "Todas") {
      throw new Error("Informe a categoria da peça.");
    }

    let price = null;

    if (
      produto.price !== null &&
      produto.price !== undefined &&
      produto.price !== ""
    ) {
      price = Number(produto.price);

      if (!Number.isFinite(price) || price < 0) {
        throw new Error("Informe um preço válido.");
      }
    }

    const id = produto.id ?? Date.now();

    if (!Number.isSafeInteger(Number(id)) || Number(id) <= 0) {
      throw new Error("O identificador da peça é inválido.");
    }

    const model = produto.modelMeasurements || {};

    return {
      ...produto,
      id: Number(id),
      name,
      category,
      price,

      photos: Array.isArray(produto.photos)
        ? produto.photos.filter(midiaValida)
        : [],

      video: midiaValida(produto.video) ? produto.video : "",

      description: String(produto.description || "").trim(),
      material: String(produto.material || "").trim(),

      colors: listaDeTextos(produto.colors),
      sizes: listaDeTextos(produto.sizes),
      ready: listaDeTextos(produto.ready),

      availability: ["consult", "ready", "order"].includes(
        produto.availability
      )
        ? produto.availability
        : "consult",

      productionTime: String(produto.productionTime || "").trim(),
      fit: String(produto.fit || "").trim(),

      modelMeasurements: {
        height: String(model.height || "").trim(),
        bust: String(model.bust || "").trim(),
        waist: String(model.waist || "").trim(),
        hips: String(model.hips || "").trim()
      },

      measurements: String(produto.measurements || "").trim(),
      care: String(produto.care || "").trim(),

      published: produto.published !== false,

      createdAt: produto.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  async function consultarAPI() {
    const resposta = await fetch(`${API_URL}/produtos/`);

    if (!resposta.ok) {
      throw new Error(
        "Não foi possível consultar os produtos no backend."
      );
    }

    const produtos = await resposta.json();

        function converterLista(valor) {
      if (Array.isArray(valor)) return valor;

      if (typeof valor === "string") {
        try {
          const lista = JSON.parse(valor);
          return Array.isArray(lista) ? lista : [];
        } catch {
          return [];
        }
      }

      return [];
    }

    return produtos.map(produto => ({
      id: produto.id,
      name: produto.nome,
      category: produto.categoria,
      price: produto.preco,

      description: produto.descricao || "",
      material: produto.material || "",

      productionTime: produto.prazo_producao || "",
      fit: produto.caimento || "",

      photos: Array.isArray(produto.fotos) ? produto.fotos : [],
      video: produto.video || "",

      colors: converterLista(produto.cores),
      sizes: converterLista(produto.tamanhos),
      ready: converterLista(produto.combinacoes_pronta_entrega),

      availability: produto.disponivel
        ? "ready"
        : "consult",

      modelMeasurements: {
        height: produto.altura_modelo || "",
        bust: produto.busto_modelo || "",
        waist: produto.cintura_modelo || "",
        hips: produto.quadril_modelo || ""
      },

      measurements: produto.medidas_peca || "",
      care: produto.cuidados || "",

      published: Boolean(produto.publicado),

      createdAt: produto.criado_em || "",
      updatedAt: produto.atualizado_em || ""
    }));
  }

  async function listarProdutos() {
    const produtos = await consultarAPI();

    return produtos.sort((a, b) => b.id - a.id);
  }

  async function buscarProduto(id) {
    const produtos = await consultarAPI();

    return produtos.find(
      produto => Number(produto.id) === Number(id)
    ) || null;
  }

  async function salvarProduto(dados) {
    const produto = normalizarProduto(dados);

    const editando =
      dados.id !== undefined &&
      dados.id !== null &&
      dados.id !== "";

    
 
    const corpo = {
      nome: produto.name,
      categoria: produto.category,
      preco: produto.price ?? 0,
      descricao: produto.description,
      material: produto.material,
      disponivel: produto.availability !== "consult",
      publicado: produto.published,

      prazo_producao: produto.productionTime,
      altura_modelo: produto.modelMeasurements.height,
      busto_modelo: produto.modelMeasurements.bust,
      cintura_modelo: produto.modelMeasurements.waist,
      quadril_modelo: produto.modelMeasurements.hips,
      medidas_peca: produto.measurements,
      informacoes_tamanho: produto.fit,
      video: typeof produto.video === "string" ? produto.video : "",

      cores: produto.colors,
      tamanhos: produto.sizes,
      combinacoes_pronta_entrega: produto.ready,
      cuidados: produto.care
    };


    const url = editando
      ? `${API_URL}/produtos/${Number(dados.id)}`
      : `${API_URL}/produtos/`;

    const resposta = await fetch(url, {
      method: editando ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(corpo)
    });

    if (!resposta.ok) {
      const erro = await resposta.text();

      throw new Error(
        `Erro ao ${editando ? "atualizar" : "cadastrar"} produto: ${erro}`
      );
    }

    const salvo = await resposta.json();

    return {
      ...produto,
      id: salvo.id,
      createdAt: salvo.criado_em || produto.createdAt,
      updatedAt: salvo.atualizado_em || produto.updatedAt
    };
  }

  async function excluirProduto(id) {
    const resposta = await fetch(
      `${API_URL}/produtos/${Number(id)}`,
      { method: "DELETE" }
    );

    if (!resposta.ok) {
      const erro = await resposta.text();

      throw new Error(`Erro ao excluir produto: ${erro}`);
    }

    return true;
  }

  return {
    listarProdutos,
    buscarProduto,
    salvarProduto,
    excluirProduto,
    consultarAPI
  };
})();
