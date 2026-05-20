import datetime
import random

import pandas as pd

# Seed para garantir a reprodutibilidade dos dados
"""
Componentes
Periféricos
"""
random.seed(42)

brands = [
    "Lenovo",
    "ASUS",
    "Acer",
    "Dell",
    "HP",
    "Samsung",
    "Apple",
    "LG",
    "Xiaomi",
    "Sony",
    "Corsair",
    "Razer",
    "Kingston",
    "Logitech",
    "Intel",
    "AMD",
    "NVIDIA",
    "Gigabyte",
    "MSI",
    "HyperX",
    "Crucial",
    "Western Digital",
    "Seagate",
    "TP-Link",
]

product_templates = [
    {
        "type": "Notebook",
        "templates": ["Notebook {brand} {model}", "Notebook Gamer {brand} {model}"],
        "category": "Eletronicos Nacionais",
        "specs": ['{ram}GB RAM, SSD {ssd}GB, Tela {tela}"', "{ram}GB RAM, {processor}, Placa {gpu}"],
        "base_cost": (2000, 7000),
    },
    {
        "type": "Smartphone",
        "templates": ["Smartphone {brand} {model}", "{brand} {model} Pro"],
        "category": "Eletronicos Nacionais",
        "specs": ["{ram}GB RAM, {ssd}GB Armazenamento, Câmera Tripla", 'Tela {tela}", Bateria de Longa Duração'],
        "base_cost": (800, 5000),
    },
    {
        "type": "Monitor",
        "templates": ["Monitor Gamer {brand} {model}", "Monitor {brand} {model} IPS"],
        "category": "Perifericos",
        "specs": ['{tela}" 144Hz 1ms', '{tela}" 4K Ultra HD, Slim'],
        "base_cost": (500, 2500),
    },
    {
        "type": "Teclado Mecânico",
        "templates": ["Teclado Mecânico {brand} {model}", "Teclado Gamer RGB {brand}"],
        "category": "Perifericos",
        "specs": ["Switch Blue, Backlight RGB", "Switch Red, Layout ABNT2, Wireless"],
        "base_cost": (150, 600),
    },
    {
        "type": "Placa de Vídeo",
        "templates": ["Placa de Vídeo {brand} {model}", "GPU {brand} {model} OC Edition"],
        "category": "Componentes",
        "specs": ["{ram}GB VRAM GDDR6, Ray Tracing", "Dual Fan, Suporte PCI-E 4.0"],
        "base_cost": (1200, 9000),
    },
]

models_pool = [
    "X1",
    "Pro",
    "Air",
    "Max",
    "Ultra",
    "Plus",
    "LOQ",
    "Legion",
    "Predator",
    "TUF",
    "ROG",
    "Strix",
    "Vengeance",
    "Evo",
    "Core i7",
    "RTX 4060",
]
processors_pool = ["Intel i5 12ª Geração", "Intel i7 13ª Geração", "AMD Ryzen 5 5600X"]
gpus_pool = ["GeForce RTX 3050 6GB", "GeForce RTX 4060 8GB", "Radeon RX 6600 8GB"]
fornecedores = ["Garrido Fornecimento", "TechDistri", "Eletronica Norte", "Conecta Distribuidora", "Global Tech"]
publico_options = ["sim", "nao"]

data = []
current_time = datetime.datetime(2026, 5, 20, 20, 8)

for _ in range(1000):
    pt = random.choice(product_templates)
    brand = random.choice(brands)
    model = random.choice(models_pool)
    template = random.choice(pt["templates"])

    ram = random.choice([8, 16, 32])
    ssd = random.choice([256, 512, 1000])
    tela = random.choice([14, 15.6, 24, 27])
    processor = random.choice(processors_pool)
    gpu = random.choice(gpus_pool)

    nome = template.format(brand=brand, model=model, ram=ram, ssd=ssd, tela=tela)
    spec_template = random.choice(pt["specs"])
    spec_text = spec_template.format(ram=ram, ssd=ssd, tela=tela, processor=processor, gpu=gpu)

    descricao = f"{pt['type']} {brand} {model}, com {spec_text}."
    preco_custo = round(random.uniform(pt["base_cost"][0], pt["base_cost"][1]), 2)
    preco = round(preco_custo * random.uniform(1.2, 1.8), 2)

    estoque = random.randint(5, 150)
    estoque_minimo = random.randint(2, min(20, estoque))

    categorias = pt["category"]
    fornecedor = random.choice(fornecedores)
    publico = random.choices(publico_options, weights=[0.85, 0.15])[0]

    time_offset = random.randint(-60, 0)
    created_date = current_time + datetime.timedelta(days=time_offset, minutes=random.randint(0, 1440))
    updated_date = created_date + datetime.timedelta(days=random.randint(0, abs(time_offset)))

    data.append(
        {
            "nome": nome,
            "descricao": descricao,
            "preco": preco,
            "preco_custo": preco_custo,
            "estoque": estoque,
            "estoque_minimo": estoque_minimo,
            "categorias": categorias,
            "fornecedor": fornecedor,
            "publico": publico,
            "criado_em": created_date.strftime("%d/%m/%Y %H:%M"),
            "atualizado_em": updated_date.strftime("%d/%m/%Y %H:%M"),
        }
    )

df = pd.DataFrame(data)
df.to_csv("produtos_ficticios.csv", index=False, encoding="utf-8-sig")
