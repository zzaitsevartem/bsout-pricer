# BMAD — Business → Model → Architecture → Development

Директория BMAD-модулей проекта bsout.

## Структура

```
_bmad/
├── README.md                   # Этот файл
├── _config/
│   └── agent-manifest.csv      # Манифест агентов BMAD
│
├── core/                       # Ядро BMAD
│   ├── agents/                 #   bmad-master агент
│   ├── tasks/                  #   Базовые задачи (help, review, editorial)
│   └── workflows/              #   Базовые воркфлоу (party-mode, brainstorming)
│
├── bmm/                        # Business Model Maturity
│   ├── agents/                 #   9 агентов (analyst, architect, dev, pm, qa, sm, ux-designer, tech-writer, quick-flow-solo-dev)
│   └── workflows/              #   23 воркфлоу (анализ, планирование, решение, реализация)
│
├── bmb/                        # BMAD Module Builder
│   ├── agents/                 #   3 агента (agent-builder, module-builder, workflow-builder)
│   └── workflows/              #   12 воркфлоу (создание/редактирование/валидация)
│
├── cis/                        # Creative Innovation & Strategy
│   ├── agents/                 #   6 агентов (brainstorming, problem-solving, design-thinking, innovation, presentation, storytelling)
│   └── workflows/              #   5 воркфлоу (brainstorming, problem-solving, storytelling, design-thinking, innovation-strategy)
│
├── tea/                        # Testing & Education Automation
│   ├── agents/                 #   1 агент (tea)
│   └── workflows/              #   10 воркфлоу (atdd, automate, ci, framework, nfr, test-design, test-review, trace, teach-me-testing)
│
├── discovery/                  # Артефакты discovery-фазы
├── product/                    # Артефакты product/UX-фазы
├── architecture/               # Артефакты архитектурной фазы
├── story-prep/                 # Артефакты фазы подготовки stories
├── implementation/             # Артефакты фазы реализации
├── qa/                         # Артефакты фазы QA
└── handoff/                    # Артефакты фазы handoff
```

## Workflow

```
Пользователь → Discovery → Product/UX → Architecture → Story Prep → Implementation → QA → Handoff
```

Каждая фаза создаёт артефакт в своей директории. Контракты выходов описаны в `docs/agents/agent-output-contracts.md`.

## Модули

| Модуль | Описание | Агентов | Воркфлоу |
|--------|----------|---------|----------|
| **core** | Ядро BMAD — базовые агенты, задачи и воркфлоу | 1 | 2 |
| **bmm** | Business Model Maturity — полный цикл разработки продукта | 9 | 23 |
| **bmb** | BMAD Module Builder — создание и поддержка BMAD-модулей | 3 | 12 |
| **cis** | Creative Innovation & Strategy — креативные и стратегические методики | 6 | 5 |
| **tea** | Testing & Education Automation — тестирование и обучение | 1 | 10 |
