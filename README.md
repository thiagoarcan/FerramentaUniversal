# Ferramenta Universal de Precisão

Aplicação HTML offline de marcenaria que reúne dois projetistas de esquadros e dois croquis interativos de serra-copo.

## Executar
Abra [Oficina_Precisao_Universal.html](Oficina_Precisao_Universal.html) diretamente no navegador. HTML, CSS e JavaScript estão no mesmo arquivo; não há instalação, conexão de rede nem layout específico para Galaxy Flip.

## Módulos
- Projetos de esquadros: geometria, dimensões, proporções, material, espessura e cotas.
- Croquis de serra-copo: desenhos parametrizáveis de furos, diâmetros, sobreposições e bordas.

## Estrutura
- `Oficina_Precisao_Universal.html`: aplicativo multipropósito pronto para uso.
- `source_html/`: quatro versões originais preservadas.
- `build_oficina_universal.py`: gerador do HTML consolidado.
- `tests/oficina_static.test.js`: testes estáticos e geométricos.
- `tests/oficina_universal.test.js`: testes de interface com Playwright.

## Testes
```bash
node --test tests/oficina_static.test.js
```

Testes de navegador precisam de Playwright e de um Chromium compatível instalado.

## Fabricação
Confira medidas, tolerâncias, estabilidade e segurança antes de cortar ou usinar peças.
