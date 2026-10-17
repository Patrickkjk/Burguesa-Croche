const CONFIG = {
  // Nome da loja
  storeName: "Burguesa Crochê",

  // Endereço do backend
  apiUrl: "http://127.0.0.1:8000",

  // WhatsApp: país + DDD + número, somente números
  whatsapp: "5573999638014",

  // Instagram: somente o nome de usuário, sem @
  instagram: "burguesa.croche2",

  // Deixe vazio enquanto não houver um e-mail definido
  email: "",

  // Informação da promoção exibida no atendimento
  firstPurchaseCoupon: "10% OFF",

  // Preencher com o prazo real antes de divulgar.
  // Vazio significa que o prazo deve ser consultado.
  productionTime: "",

  // Mensagem inicial do atendimento geral
  defaultMessage:
    "Olá! Vim pelo catálogo da Burguesa Crochê e gostaria de saber mais sobre as peças.",

  // Chaves para identificar os dados locais deste projeto
  storage: {
    favorites: "burguesa-favoritos-v1",
    database: "burguesa-croche",
    databaseVersion: 1
  }
};