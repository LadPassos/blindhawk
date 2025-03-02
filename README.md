# ⚡ CAPTCHA de Áudio Seguro com FastAPI

LINK PROJETO HOSPEADO PARA DEMONSTRAÇAO - https://blindhawk.fly.dev

## 📗 Sobre o Projeto
Este projeto foi desenvolvido como parte da disciplina **Segurança em Aplicações** e tem como objetivo criar um **sistema de CAPTCHA baseado em áudio** utilizando **FastAPI**, IA e boas práticas de segurança. Ele visa impedir ataques automatizados (“bots”) em aplicações web, garantindo acessibilidade para usuários com deficiência visual.

## 🔧 Tecnologias Utilizadas
- **FastAPI** - Framework para desenvolvimento da API.
- **Sentence Transformers** - IA para comparação de similaridade semântica.
- **gTTS (Google Text-to-Speech)** - Conversão de texto para áudio.
- **Pydub** - Manipulação de áudio e adição de ruídos.
- **Redis** - Rate limiting para evitar abusos.
- **FastAPI Limiter** - Controle de requisições para segurança.
- **Freesound API** - Geração de áudio dinâmica.
- **NLTK** - Processamento de linguagem natural.
- **HTML/CSS/JS** - Interface gráfica para interação com o CAPTCHA.

## ⛓️ Funcionalidades
- Geração de CAPTCHA em áudio usando IA e sons aleatórios.
- Verificação baseada em **similaridade semântica** (usuário não precisa digitar exatamente o que ouviu).
- **Adiciona ruído adversário** ao áudio para dificultar ataques automatizados.
- Implementa **rate limiting** (5 requisições/minuto) para evitar ataques de força bruta.
- Proteção contra ataques XSS, CSRF e replay com tokens de sessão.
- Interface responsiva com botões acessíveis para ouvir e validar o CAPTCHA.

## ⚙️ Configuração do Projeto
### 1. Clonar o Repositório
```bash
git clone https://github.com/seuusuario/captcha-audio-seguro.git
cd captcha-audio-seguro
```

### 2. Criar um Ambiente Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

Caso esteja usando macOS, instale o FFmpeg para suporte ao Pydub:
```bash
brew install ffmpeg
```

### 4. Iniciar o Redis (Rate Limiting)
```bash
redis-server
```

### 5. Baixar Corpus do NLTK
```python
import nltk
nltk.download('mac_morpho')
```

### 6. Rodar o Servidor
```bash
uvicorn main:app --reload
```

Acesse em: **http://127.0.0.1:8000**

## 📝 Endpoints da API
| Método | Rota | Descrição |
|---------|------|------------|
| `GET` | `/audio-captcha` | Gera um CAPTCHA de áudio e retorna um token de sessão. |
| `POST` | `/verify-captcha` | Verifica a resposta do usuário e valida o CAPTCHA. |

Acesse a documentação interativa em: **http://127.0.0.1:8000/docs**

## ✨ Interface Web
O projeto inclui uma interface web responsiva para interagir com o CAPTCHA. Basta abrir o arquivo `index.html` no navegador ou servir o arquivo pelo FastAPI.

## ⛓️ Medidas de Segurança Implementadas
- **Rate Limiting**: Bloqueia acessos excessivos (5 requisições/minuto).
- **Criptografia**: Dados são protegidos com `Fernet`.
- **Sessões Seguras**: Cada CAPTCHA tem um token de sessão único.
- **Headers de Segurança**: Proteção contra clickjacking e sniffing.
- **Dificuldade para Bots**: Uso de IA para verificação semântica e ruído adversário no áudio.

## 🔒 Formas de Quebra do CAPTCHA e Contramedidas
✅ 1. Reconhecimento de Áudio via IA

⚠️ Forma de Quebra

Algoritmos como Google Speech-to-Text, CMU Sphinx ou DeepSpeech podem ser utilizados para transcrever automaticamente o áudio do CAPTCHA e responder sem interação humana.

⚖️ Contramedidas

Adicionação de Ruído Branco ao áudio, dificultando a transcrição por IA.

Mistura de Sons Aleatórios do Freesound.org, impedindo que apenas fala seja interpretada.

2. Reutilização de CAPTCHA

⚠️ Forma de Quebra

Um atacante pode capturar o áudio de um CAPTCHA já resolvido e reutilizá-lo para burlar o sistema.

⚖️ Contramedidas

Session Tokens Únicos: Cada CAPTCHA tem um identificador exclusivo que impede reutilização.

Expiração Rápida: Cada CAPTCHA só é válido por 120 segundos.

Hashing da Resposta: A resposta correta não é armazenada em texto simples.

3. Ataques por Força Bruta

⚠️ Forma de Quebra

Um bot pode tentar várias respostas até acertar a correta.

⚖️ Contramedidas

Rate Limiting: Restrito a 5 tentativas por minuto.

Bloqueio Progressivo: Após 5 erros, o tempo de espera aumenta exponencialmente.

Limite de Entrada: Apenas respostas com até 100 caracteres são aceitas.

Variação do Tom e Velocidade para evitar treinamento de modelos automatizados.

 4. Ataques Baseados em Similaridade

⚠️ Forma de Quebra

Bots podem tentar palavras semelhantes, baseando-se em correlação semântica.

⚖️ Contramedidas

Threshold de Similaridade: Apenas respostas acima de 60% de similaridade são aceitas.

Normalização do Texto: Remove acentos, caracteres especiais e padroniza para minúsculas.

5. Engenharia Reversa na API

⚠️ Forma de Quebra

Inspeção das respostas da API para detectar padrões e automatizar a resolução do CAPTCHA.

⚖️ Contramedidas

Headers de Segurança: Implementados X-Frame-Options, Strict-Transport-Security, entre outros.

CORS Restritivo: Apenas origens confiáveis podem acessar a API.

Criptografia da Resposta: Respostas podem ser armazenadas criptografadas usando Fernet.

## Este projeto implementa múltiplas camadas de segurança para dificultar a automação da resolução do CAPTCHA, protegendo contra ataques automatizados e melhorando a segurança das aplicações web.

## 🚀 Melhorias Futuras
- Adicionar suporte a CAPTCHA visual para opção híbrida.
- Implementar um **painel de administração** para monitorar tentativas.
- Melhorar integração com **bancos de dados** para registro de logs de tentativas.

## 👥 Equipe
- **Luiz Alberto dos Passos**
---

Este projeto foi desenvolvido para fins educacionais, destacando boas práticas de segurança em aplicações web. 
Assim que avaliado pelo professor da disciplina esse repositorio vai ser privado 🌟
