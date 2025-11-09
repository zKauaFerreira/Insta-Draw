# 🎨 Insta-Draw: Automação de Desenho para Instagram

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 🌟 Introdução

Bem-vindo ao **Insta-Draw**! Este projeto é uma ferramenta poderosa para transformar suas imagens em traços artísticos e automatizar o desenho desses traços diretamente na tela do seu dispositivo Android, ideal para criar stories ou posts únicos no Instagram.

Com o Insta-Draw, você pode:
- Remover o fundo de imagens.
- Aplicar filtros Canny para extrair contornos.
- Ajustar brilho, desfoque e limiares para refinar os traços.
- Automatizar o desenho na tela do seu Android, simulando toques e arrastes.

Prepare-se para levar sua criatividade no Instagram para o próximo nível! ✨

## 🚀 Funcionalidades

-   **🖼️ Processamento de Imagens:**
    -   Carregue imagens nos formatos PNG, JPG, JPEG, BMP, WEBP.
    -   Remoção de fundo inteligente (requer `rembg`).
    -   Extração de contornos com o algoritmo Canny, com ajustes de limiar e desfoque.
    -   Ajuste de brilho para a imagem de fundo.
    -   Modo "apenas traços" para visualização em preto e branco.
-   **🖌️ Edição Interativa:**
    -   Ferramenta de borracha/restauração para refinar manualmente os traços.
    -   Funcionalidade de corte (crop) para focar em áreas específicas da imagem.
    -   Zoom interativo para detalhes.
    -   Desfazer/Refazer ilimitado para todas as ações de edição.
-   **🤖 Automação de Desenho:**
    -   Integração com ADB (Android Debug Bridge) para controle do dispositivo Android.
    -   Definição interativa da área de desenho na tela do desktop.
    -   Escalonamento e centralização automáticos dos traços para a área de desenho.
    -   Simulação de toques e arrastes para desenhar os traços no Android.
    -   Pausas configuráveis durante o desenho para evitar travamentos do aplicativo.
    -   Cancelamento do desenho a qualquer momento com a tecla `ESC`.

## 📋 Pré-requisitos

Este projeto foi desenvolvido e testado primariamente no **Pop!_OS (Linux)**. Embora não tenha sido exaustivamente testado em outros sistemas operacionais, as bibliotecas Python utilizadas (`pyautogui`, `adb`, `tkinter`, `opencv-python`, `numpy`, `Pillow`, `rembg`, `pynput`) são, em sua maioria, **multiplataforma**.

Portanto, o Insta-Draw **deve ser compatível** com os seguintes sistemas operacionais:

-   **🐧 Linux** (Pop!_OS, Ubuntu, Fedora, etc.)
-   **🍎 macOS**
-   **🪟 Windows**

No entanto, usuários de macOS e Windows podem precisar de configurações específicas para o ADB e, possivelmente, para as permissões do `pynput` (para a tecla ESC) em seus respectivos ambientes.

Para rodar o Insta-Draw, você precisará do seguinte:

### 🐍 Python 3.10+ e Dependências

Certifique-se de ter o Python 3.10 ou superior instalado. Em seguida, instale as bibliotecas Python necessárias:

```bash
pip install -r requirements.txt
```

### 📱 ADB (Android Debug Bridge) e Dispositivo Android

O coração da automação é o ADB. Você precisará de:

1.  **ADB Instalado:** Siga as instruções para instalar o ADB em seu sistema operacional.
    -   **Windows:** [Guia de Instalação ADB](https://www.xda-developers.com/install-adb-windows-mac-linux/)
    -   **macOS:** [Guia de Instalação ADB](https://www.xda-developers.com/install-adb-windows-mac-linux/)
    -   **Linux:** [Guia de Instalação ADB](https://www.xda-developers.com/install-adb-windows-mac-linux/)

    **Recomendação:** Para uma experiência mais fluida e sem a necessidade de um dispositivo físico, recomendo usar um emulador Android como o **Genymotion**. Ele oferece uma integração excelente com o ADB.

2.  **Dispositivo Android (Físico ou Emulador):**
    -   **Modo Desenvolvedor Ativado:** No seu dispositivo Android, vá em `Configurações` > `Sobre o telefone` e toque no `Número da build` (ou `Versão MIUI` / `Número da Versão`) várias vezes até ver a mensagem "Você agora é um desenvolvedor!".
    -   **Depuração USB Ativada:** Em `Configurações` > `Sistema` > `Opções do desenvolvedor`, ative a `Depuração USB`.
    -   **Autorizar Conexão ADB:** Conecte seu dispositivo ao computador via USB. Uma mensagem de "Permitir depuração USB?" aparecerá. Autorize a conexão.
    -   **Verificar Conexão:** Abra seu terminal e execute:
        ```bash
        adb devices
        ```
        Você deverá ver seu dispositivo listado.

## 🛠️ Como Usar

Siga estes passos para usar o Insta-Draw:

1.  **Inicie a Aplicação:**
    ```bash
    python3 main.py
    ```
    A interface gráfica do Insta-Draw será aberta.

2.  **Carregue sua Imagem:**
    -   Clique no botão "Carregar Imagem" e selecione a imagem que deseja processar.

3.  **Processe e Edite (Opcional):**
    -   Use os sliders e botões na interface para:
        -   "Remover Fundo" (se `rembg` estiver instalado).
        -   Ajustar "Limiar Canny" e "Desfoque" para refinar os traços.
        -   Ajustar "Brilho" da imagem de fundo.
        -   Ativar "Apenas Traços" para ver o resultado final dos contornos.
        -   Use a "Borracha" ou "Restaurar" para editar manualmente a imagem.
        -   Use a ferramenta de "Cortar" para selecionar uma área específica.
    -   Clique em "Atualizar Preview" para ver as mudanças.

4.  **Salve os Traços:**
    -   Quando estiver satisfeito com os traços, clique em "Salvar Traços".
    -   **IMPORTANTE:** Uma janela de overlay transparente aparecerá na sua tela. **Use o mouse para arrastar e desenhar um retângulo** que corresponda à área exata onde você deseja que o desenho seja feito na tela do seu Android (onde o Instagram estará aberto). Confirme a seleção.
    -   Este passo é crucial para que o script saiba onde desenhar.

5.  **Prepare o Instagram no Android:**
    -   No seu dispositivo Android (físico ou emulador), abra o Instagram.
    -   **Navegue até a tela de conversa onde você deseja desenhar.**
    -   **Certifique-se de que a tela de desenho do Instagram esteja visível e pronta para receber os traços.**

6.  **Inicie a Automação de Desenho:**
    -   De volta ao Insta-Draw, clique no botão "Iniciar Automação de Desenho".
    -   O script irá:
        -   Conectar-se ao seu dispositivo Android via ADB.
        -   Navegar automaticamente para a ferramenta de desenho do Instagram (clicando em "More" e "Draw").
        -   Ajustar a espessura do pincel para o mais fino.
        -   Selecionar o pincel "Sharpie".
        -   Começar a desenhar os traços na tela do Android, respeitando a área que você definiu no passo 4.
    -   **NÃO MOVA O MOUSE OU INTERAJA COM O COMPUTADOR/CELULAR DURANTE ESTE PROCESSO!**
    -   Você pode pressionar `ESC` no terminal a qualquer momento para cancelar o desenho.

## ⚙️ Configuração

Você pode ajustar a velocidade do desenho e as pausas para melhor se adequar ao seu dispositivo e evitar travamentos.

No arquivo `src/automation/draw_automation.py`, você pode modificar:

-   `speed_level`: Define a velocidade geral do desenho. Opções: `'slow'`, `'medium'`, `'fast'`, `'very_fast'`. (`'medium'` é o padrão e recomendado).
-   `strokes_per_chunk`: Número de traços desenhados antes de uma pausa longa. (Padrão: `70` para aproximadamente 1 minuto).
-   `chunk_break_time`: Duração da pausa em segundos entre os chunks de traços. (Padrão: `3` segundos).

Exemplo de ajuste:

```python
            draw_strokes_with_pyautogui(
                traces_data,
                drawing_area,
                speed_level="medium", # Altere aqui para 'slow', 'fast', etc.
                strokes_per_chunk=70, # Altere para mais ou menos traços por pausa
                chunk_break_time=3,   # Altere a duração da pausa
            )
```

## ⚠️ Solução de Problemas

-   **`NameError: name 'REMBG_AVAILABLE' is not defined`**: Certifique-se de que a biblioteca `rembg` está instalada (`pip install rembg`). Se o erro persistir, pode haver um problema na detecção da biblioteca.
-   **`ImportError: attempted relative import with no known parent package`**: Este erro ocorre se você tentar executar um script interno diretamente. Sempre inicie a aplicação via `python3 main.py`.
-   **Desenho não inicia ou falha no ADB**:
    -   Verifique se o ADB está corretamente instalado e seu dispositivo está conectado e autorizado (`adb devices`).
    -   Certifique-se de que a Depuração USB está ativada nas Opções do Desenvolvedor do Android.
    -   Reinicie o servidor ADB (`adb kill-server` e depois `adb start-server`).
    -   Verifique se o Instagram está na tela correta (conversa/story com a ferramenta de desenho ativa).
-   **Instagram trava ou fecha durante o desenho**:
    -   Tente usar um `speed_level` mais lento (ex: `'slow'`).
    -   Aumente o `chunk_break_time` ou diminua o `strokes_per_chunk` em `src/automation/draw_automation.py` para pausas mais frequentes/longas.
    -   Certifique-se de que seu dispositivo Android (físico ou emulador) tem recursos suficientes.

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Se você tiver ideias, melhorias ou encontrar bugs, sinta-se à vontade para abrir uma issue ou enviar um Pull Request.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

Feito com ❤️ por Kauã Ferreira.
