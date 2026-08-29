# GnTech Weather API

API REST para coleta, persistência e consulta de dados climáticos utilizando a OpenWeather API.

## Objetivo

O projeto demonstra a construção de uma API organizada em camadas, capaz de consultar condições climáticas atuais, normalizar a resposta do serviço externo e armazenar os dados para consultas posteriores. A aplicação inclui documentação OpenAPI, ambiente reproduzível com Docker e testes automatizados sem dependência de chamadas externas reais.

## Tecnologias

- Python
- Django
- Django REST Framework
- PostgreSQL
- Docker e Docker Compose
- OpenWeather API
- drf-spectacular, OpenAPI e Swagger
- Git

## Arquitetura

```text
Cliente -> Django REST API -> OpenWeather API
                    |
                    +-> PostgreSQL
```

A integração externa fica isolada da camada de serviço responsável pela persistência. As views REST validam as requisições, acionam o serviço e traduzem os resultados e erros para respostas HTTP.

## Estrutura principal

```text
.
├── config/                       # Configurações e rotas principais do Django
├── weather/
│   ├── migrations/               # Histórico do schema da aplicação
│   ├── services/
│   │   ├── openweather.py        # Cliente e normalização da OpenWeather
│   │   └── weather_service.py    # Orquestração e persistência
│   ├── tests/                    # Testes da integração, serviço e endpoints
│   ├── models.py                 # Modelo de registro climático
│   ├── serializers.py            # Validação e representação dos dados
│   ├── urls.py                   # Rotas do domínio weather
│   └── views.py                  # Endpoints REST
├── .env.example                  # Modelo de configuração sem credenciais
├── Dockerfile                    # Imagem da aplicação
├── docker-compose.yml            # Serviços web e PostgreSQL
├── manage.py
└── requirements.txt
```

## Pré-requisitos

- Docker
- Docker Compose
- Conta e chave de API da [OpenWeather](https://openweathermap.org/api)

## Configuração e execução

Clone o repositório e acesse o diretório do projeto:

```bash
git clone https://github.com/alexsandrodrummer/gntech-weather-api.git
cd gntech-weather-api
```

Crie o arquivo local de variáveis de ambiente:

```bash
cp .env.example .env
```

Abra o `.env` e substitua os placeholders. Em especial, defina `OPENWEATHER_API_KEY` com a chave obtida na sua conta OpenWeather. Não utilize credenciais reais no `.env.example`.

As variáveis utilizadas são:

```dotenv
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
POSTGRES_DB=gntech_weather
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
OPENWEATHER_API_KEY=your-openweather-api-key
```

Dentro do Docker Compose, `POSTGRES_HOST` é definido automaticamente como `db`, nome do serviço PostgreSQL.

Construa as imagens e inicie a aplicação:

```bash
docker compose up --build
```

O serviço web aguarda o banco ficar saudável, executa as migrations e inicia o Django na porta `8000`.

## URLs

- API: <http://localhost:8000/api/weather/>
- Swagger UI: <http://localhost:8000/api/docs/>
- OpenAPI schema: <http://localhost:8000/api/schema/>

## Endpoints

### Coletar dados climáticos

```http
POST /api/weather/collect/
Content-Type: application/json
```

Body:

```json
{
  "city": "Campinas"
}
```

Em caso de sucesso, o endpoint consulta a OpenWeather, persiste o registro e responde com HTTP `201 Created`:

```json
{
  "id": 1,
  "city": "Campinas",
  "country": "BR",
  "temperature": 24.5,
  "feels_like": 25.1,
  "humidity": 70,
  "pressure": 1015,
  "weather_description": "clear sky",
  "wind_speed": 3.2,
  "collected_at": "2026-08-29T14:45:18.915535Z"
}
```

### Listar registros

```http
GET /api/weather/
```

Retorna HTTP `200 OK` com uma lista de registros climáticos. Quando não há dados, retorna uma lista vazia.

### Consultar um registro

```http
GET /api/weather/<id>/
```

Retorna HTTP `200 OK` para um registro existente ou `404 Not Found` quando o identificador não é encontrado.

Os contratos completos e demais respostas de erro podem ser consultados no Swagger UI.

## Testes automatizados

Execute a suíte no ambiente Docker:

```bash
docker compose run --rm web python manage.py test
```

A suíte atual possui 20 testes automatizados, cobrindo:

- integração com a OpenWeather;
- camada de serviço;
- persistência de registros;
- endpoints REST;
- validações e cenários de erro.

Todas as chamadas à OpenWeather são simuladas com mocks. Assim, os testes não acessam a internet, não consomem a cota da API e produzem resultados determinísticos.

## Decisões técnicas

- **Separação de responsabilidades:** integração externa, serviço de aplicação e camada REST permanecem independentes, facilitando manutenção e testes.
- **Configuração por ambiente:** credenciais e configurações sensíveis são fornecidas por variáveis de ambiente.
- **Persistência:** o PostgreSQL executa em container e utiliza volume nomeado para preservar os dados entre reinicializações.
- **Inicialização confiável:** o healthcheck do banco impede que a aplicação inicie antes de o PostgreSQL estar pronto.
- **Documentação:** o drf-spectacular gera o schema OpenAPI e disponibiliza uma interface Swagger navegável.
- **Falhas externas:** timeout, conexão, autenticação, cidade inexistente e respostas inválidas são convertidos em exceções específicas e respostas HTTP adequadas.

## Segurança

- O arquivo `.env` não é versionado.
- Chaves de API, senhas e secrets não ficam no código ou nos arquivos Docker.
- O `.env.example` contém somente placeholders e valores apropriados para configuração local.
