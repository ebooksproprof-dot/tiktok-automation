# Avatar4.1 — investigação limitada e estado verificável

Data:22/10/2026. Nenhum avatar animado foi gerado nesta avaliação. Nenhum modelo
pesado foi instalado, nenhum aceite adicional foi realizado, nenhum custo pago.
Um retrato original eventualmente criado é um asset de identidade, não uma prova
de boca sincronizada, movimentos corporais ou integração em produção.

## Resultado por motor

|Motor|Evidência oficial|Decisão nesta infraestrutura|
|---|---|---|
|SadTalker|inference.py possui --cpu; modelo256/512 de725.066.984bytes e mapping155.521.183/155.779.231bytes; licença geralApache2.0 com ressalva de componentes terceiros|CandidatoCPU não executado: autorização comercial dos assets BFM não esclarecida; sem benchmarkCPU. Não declarar inviabilidade universal|
|MuseTalk|Setup oficial recomendaPython3.10/CUDA11.7; exemplo8s≈5min emRTX3050Ti4GB; códigoMIT e modelo permite uso comercial, dependências separadas|Não adotado no runnerCPU; tempoGPU não é estimativaCPU|
|Wav2Lip oficial|README restringe uso a pessoal/pesquisa/não comercial|Não adotado para vídeos comerciais|
|LivePortrait|MIT, mas LICENSE exige substituir modelosInsightFace não comerciais; animação guiada por movimento não comprova fala nova sincronizada|Não adotado sem substituir detector, fornecer driver e validar sincronismoCPU|

Fontes primárias consultadas:
- https://github.com/OpenTalker/SadTalker/blob/main/inference.py
- https://github.com/OpenTalker/SadTalker/blob/main/LICENSE
- https://github.com/OpenTalker/SadTalker/blob/main/requirements.txt
- https://github.com/OpenTalker/SadTalker/releases/tag/v0.0.2-rc
- https://github.com/OpenTalker/SadTalker/blob/main/src/utils/init_path.py
- https://github.com/TMElyralab/MuseTalk
- https://github.com/Rudrabha/Wav2Lip/blob/master/README.md
- https://github.com/KlingAIResearch/LivePortrait/blob/main/LICENSE
- https://github.com/OpenTalker/SadTalker/blob/main/src/utils/preprocess.py
- https://github.com/OpenTalker/SadTalker/blob/main/src/face3d/util/load_mats.py
- https://github.com/sicxu/Deep3DFaceRecon_pytorch/blob/master/README.md
- https://faces.dmi.unibas.ch/bfm/content/basel_face_model/downloads/BFM_NonCommercial_License_Agreement.pdf

## Pendência específica de licença do candidato CPU

O README atual do SadTalker remove a restrição não comercial do projeto; isso
não foi ignorado. Sua licença Apache2.0, entretanto, ressalva componentes de
terceiros. O caminho de inferência `CropAndExtract.__init__` carrega
`face_3drecon` do safetensor e chama `load_lm3d(dir_of_BFM_fitting)`, que abre
`similarity_Lm3D_all.mat`. O projeto de reconstrução de origem instrui obter
BFM09 separadamente. A licença oficial BFM09 limita uso a pesquisa, avaliação
ou testes não comerciais e declara que download/uso implica concordância.

Não foi identificada uma concessão comercial separada para o asset de landmarks
distribuído e os componentes correspondentes dos pesos. Isso é uma pendência
de proveniência/licença, não uma conclusão jurídica de que todo SadTalker é
proibido. A concessão Apache do código não resolve por si só essa pendência.
Como a missão proíbe aceitar licenças adicionais e exige uso comercial, não
foram baixados os pesos, executada inferência ou acionado workflow que os use.
Próximo desbloqueio: comprovar licença comercial dos assets exatos ou fornecer
substitutos compatíveis com proveniência permissiva, antes do smoke test CPU.

## Medição local e limites

Python3.12.14; torch e cv2 ausentes tanto no Python corrente quanto no runtime
primário. nvidia-smi ausente. Memória observada pelo host≈9.967MiB total,
sem swap; isto não representa limite certificado de um runnerGitHub.
O estado real é coletado por `python automation/avatar_backend.py`.

SadTalker fixa numpy1.23.4 e scikit-image0.19.3 nas dependências oficiais. Isso
exige ambiente compatível/revalidação em vez de instalar cegamente sobre o
Python3.12 do pipeline existente. Um workflow isolado com setup-python3.10
resolve a incompatibilidade de ambiente; ela não é bloqueio definitivo.
O download mínimo principal+mapeamento é≈880MB,
fora de bibliotecas e outros modelos. Não foi medido tempo de inferência nem
qualidade da imagem/boca porque inferência não foi executada.

Não há prova nesta avaliação de uma solução que combine personagem fotorrealista,
movimento corporal, lipsync convincente,25s1080x1920,CPU gratuito e2vídeos/dia.
Isso é uma lacuna de validação concreta, não prova de impossibilidade matemática
ou de que nenhuma oferta futura poderia satisfazer o pedido.

## Arquitetura preservada

`avatar_backend.load_avatar_engine` é a interface futura e falha explicitamente
para todos os motores ainda não validados. `select_format('B')` retorna formatoC
com motivo explícito; não transforma retrato estático em alegação de avatar.
O módulo não baixa pesos, aceita licenças, chama APIs pagas ou modifica a fila.

Próxima prova técnica candidata: ambientePython3.10 isolado, pin de revisão
SadTalker e todas as licenças de dependências/pesos; retrato original+áudio2s;
256pxCPU, batch1, sem enhancer, prazo300s e memória monitorada. Registrar
falhas/timeouts e não extrapolar2s para25s sem benchmark. Só depois avaliar512px,
qualidade de boca/olhos, composição1080p, persistência e execuçãoGitHub.
Não alegar vídeo1080p nativo apenas por ampliar uma saída facial256/512px.

Enquanto não houver essa prova, formatoC com cenas reais licenciadas e voz
feminina é a alternativa operacional. A seleção e o roteiro ainda precisam de
correspondência visual; filmagens genéricas não são testes reais de produtos.
