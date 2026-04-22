export interface DemoProduct {
  id: string;
  name: string;
  category: string;
  description: string;
  priceUsd: number;
  image: string;
  highlights: string[];
}

export const DEMO_PRODUCTS: DemoProduct[] = [
  {
    id: "aurora-ring",
    name: "Anillo Aurora Halo",
    category: "Anillos",
    description: "Anillo de compromiso con halo brillante y terminacion premium para propuesta o aniversario.",
    priceUsd: 1450,
    image: "/demo-products/aurora-ring.svg",
    highlights: ["Oro blanco 14k", "Piedra central corte oval", "Entrega boutique"],
  },
  {
    id: "serena-necklace",
    name: "Collar Serena Drop",
    category: "Collares",
    description: "Collar delicado con caida elegante para regalos de ocasion y colecciones de lujo accesible.",
    priceUsd: 980,
    image: "/demo-products/serena-necklace.svg",
    highlights: ["Cadena fina ajustable", "Baño premium", "Presentacion para regalo"],
  },
  {
    id: "nova-earrings",
    name: "Aretes Nova Spark",
    category: "Aretes",
    description: "Aretes de brillo frontal pensados para bodas, eventos de noche y sets de regalo.",
    priceUsd: 720,
    image: "/demo-products/nova-earrings.svg",
    highlights: ["Cierre seguro", "Acabado espejo", "Estilo de evento"],
  },
  {
    id: "imperial-bracelet",
    name: "Pulsera Imperial Tennis",
    category: "Pulseras",
    description: "Pulsera tipo tennis con presencia premium para look formal o regalo corporativo especial.",
    priceUsd: 1320,
    image: "/demo-products/imperial-bracelet.svg",
    highlights: ["Linea continua de brillo", "Cierre reforzado", "Look formal"],
  },
  {
    id: "eclipse-set",
    name: "Set Eclipse Signature",
    category: "Sets",
    description: "Set coordinado de collar y aretes para campañas de temporada y bundles de alto valor.",
    priceUsd: 1890,
    image: "/demo-products/eclipse-set.svg",
    highlights: ["Bundle de alto ticket", "Presentacion premium", "Ideal para campaña"],
  },
  {
    id: "monaco-cuff",
    name: "Brazalete Monaco Cuff",
    category: "Brazaletes",
    description: "Brazalete abierto con identidad editorial, pensado para fotos de producto y vitrinas de lujo.",
    priceUsd: 1110,
    image: "/demo-products/monaco-cuff.svg",
    highlights: ["Statement piece", "Ajuste comodo", "Visual premium"],
  },
  {
    id: "royal-halo",
    name: "Anillo Royal Halo",
    category: "Anillos",
    description: "Anillo de coleccion con halo extendido y look bridal para muestras de alta conversion.",
    priceUsd: 1675,
    image: "/demo-products/royal-halo.svg",
    highlights: ["Linea bridal", "Alta percepcion de valor", "Pieza de conversion"],
  },
  {
    id: "soleil-pendant",
    name: "Colgante Soleil",
    category: "Colgantes",
    description: "Colgante solar con lenguaje contemporaneo para publico regalo y catalogo editorial.",
    priceUsd: 860,
    image: "/demo-products/soleil-pendant.svg",
    highlights: ["Diseño contemporaneo", "Cadena incluida", "Ideal para gifting"],
  },
  {
    id: "firenze-earrings",
    name: "Aretes Firenze Pearl",
    category: "Aretes",
    description: "Aretes con perla y acento brillante para lineas elegantes de venta recurrente.",
    priceUsd: 690,
    image: "/demo-products/firenze-earrings.svg",
    highlights: ["Perla premium", "Rotacion comercial", "Look clasico"],
  },
  {
    id: "victoria-layer",
    name: "Collar Victoria Layer",
    category: "Collares",
    description: "Collar multicapa para estilismo moderno y campañas dirigidas a compra impulsiva premium.",
    priceUsd: 1040,
    image: "/demo-products/victoria-layer.svg",
    highlights: ["Efecto multicapa", "Ideal para social ads", "Compra impulsiva premium"],
  },
];

export function findDemoProduct(productId: string) {
  return DEMO_PRODUCTS.find((product) => product.id === productId) ?? null;
}
