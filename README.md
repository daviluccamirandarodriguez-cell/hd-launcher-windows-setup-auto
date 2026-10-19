# HD Launcher v1.7.0 — atualização automática para Windows

## Como funciona para o jogador

1. Instala `HDLauncher-Setup.exe` **uma vez** (sem instalar Python).
2. Ao abrir o HD Launcher v1.7+, o programa consulta a Release mais recente no repositório público GitHub `daviluccamirandarodriguez-cell/hd-launcher-windows-setup`.
3. Se existir versão nova e ela tiver um **instalador EXE com nome esperado e SHA-256 oficial do GitHub**, o programa baixa em segundo plano para a pasta temporária.
4. Depois de conferir o tamanho e o SHA-256, o launcher fecha e executa o Inno Setup no modo silencioso; ao finalizar, o novo launcher abre sozinho.
5. Se não houver internet, o programa continua normalmente com a versão instalada. Contas e biblioteca permanecem em `%APPDATA%\HDLauncher\accounts.db`.

Em **Configurações → Atualizações automáticas**, pode desativar a verificação ao abrir ou clicar em `VERIFICAR ATUALIZAÇÕES AGORA`. Só ocorre autoatualização quando o aplicativo está instalado no Windows pelo nosso Setup (`unins000.exe`).

**Atenção:** a versão v1.6 já instalada **não** tinha atualizador. Você precisa instalar a **v1.7 uma única vez**; só depois o recurso passa a valer. Esta versão NÃO foi compilada nem testada num Windows neste ambiente; apenas validamos sintaxe e testes automatizados.

## Como gerar o Setup.exe v1.7 pelo GitHub

1. Extraia o ZIP desta entrega. Abra a pasta interna `HD-Launcher`. No seu repositório existente `hd-launcher-windows-setup`, substitua/atualize **os arquivos na raiz do repositório**, incluindo `.github/workflows/gerar-setup-windows.yml` (use GitHub Desktop para facilitar o envio da pasta oculta).
2. Faça `Commit to main` e `Push origin`. No GitHub, entre em **Actions → Gerar Setup EXE do HD Launcher**.
3. Aguarde a execução automática da compilação. Clique na execução verde e baixe o artefato `HDLauncher-Setup-v1.7.0`, extraia e teste o arquivo `HDLauncher-Setup-v1.7.0.exe` no Windows.
4. **Somente após testar:** em Actions, abra o workflow → **Run workflow**. Marque `Publicar o Setup.exe da versão atual no GitHub Releases` e execute. Essa etapa publica a Release `v1.7.0` com os dois nomes: `HDLauncher-Setup-v1.7.0.exe` (usado pelo atualizador) e `HDLauncher-Setup.exe` (link fixo do site).
5. Abra a página de **Releases** no repositório e confira a Release pública e os dois arquivos. Depois publique o ZIP separado do site na Cloudflare Pages.

Por que publicar dois arquivos? O app procura a versão com nome exato `HDLauncher-Setup-v1.8.0.exe`, `HDLauncher-Setup-v1.9.0.exe`, etc.; o site usa o link permanente `/releases/latest/download/HDLauncher-Setup.exe` (o nome permanece em todas as Releases).

## Para publicar uma v1.8 futura

Atualize a versão do app em `hd_launcher.py` (`APP_VERSION`), a versão do instalador em `setup.iss` (`ProductVersion`), e os nomes / tag esperados no workflow `.github/workflows/gerar-setup-windows.yml`, além das mensagens do script local `build_setup_windows.bat`. Execute a build, teste num Windows e só então publique a nova Release com o workflow. **A partir da v1.7 os usuários que não desligaram a atualização automática receberão a versão publicada ao abrir o launcher**.

## Limitações e segurança

- Exige **internet ao abrir** para procurar updates; o launcher ainda funciona offline.
- GitHub público deve conter uma Release publicada, não somente um artifact de Actions; artifacts de Actions são ZIPs temporários, NÃO servem para atualização automática.
- Arquivos baixados são comparados com SHA-256 exibido pela API oficial do GitHub. Sem SHA-256, com arquivo diferente, ou sem instalador com nome esperado, nenhuma instalação acontece.
- O updater confia na segurança do repositório oficial do GitHub. **Para distribuição ampla, assinar o instalador digitalmente é altamente recomendado.** Não publique releases de código não testado.
- A atualização automática só vale **para Windows**; Android usa outro processo.
- Downloads interrompidos ou falhas de rede não bloqueiam a abertura do launcher.
- Antes de testar a atualização automática com os jogadores, é importante testar uma nova versão (por exemplo, v1.8) num PC Windows, inclusive o fechamento, instalação e relançamento.
- O app possui controles locais e biblioteca; não há nuvem de contas.

## Estrutura

- `update_core.py`: consulta a API, compara versões, valida URL e SHA-256, faz download verificado.
- `update_qt.py`: thread para não congelar a interface.
- `hd_launcher.py`: inicia verificação, mostra progresso e aciona o instalador.
- `setup.iss`: Setup com relançamento automático ao atualizar silenciosamente.
- `.github/workflows/gerar-setup-windows.yml`: compila e opcionalmente publica Release.
- `test_update_core.py`: testes de segurança e atualização.

## Testes realizados

29 testes automatizados passaram (17 existentes + 12 novos). Não foram executados o PyInstaller/Inno Setup num Windows, nem uma instalação automática de verdade. Faça esse teste antes de anunciar a funcionalidade como concluída aos usuários.
