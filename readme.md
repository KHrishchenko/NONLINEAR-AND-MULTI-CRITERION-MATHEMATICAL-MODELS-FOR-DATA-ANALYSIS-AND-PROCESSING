# Chapter 4: Flexible Job Shop Scheduling

## Опис

Цей розділ містить приклади для задачі планування у гнучкому виробничому середовищі
(Flexible Job Shop Scheduling Problem, FJSP). У репозиторії є два підходи:

- точна оптимізація за допомогою OR-Tools CP-SAT;
- навчання агентів Reinforcement Learning на основі PPO, Maskable PPO, Recurrent PPO
  та Recurrent Maskable PPO.

Реалізація поєднаного recurrent-maskable підходу базується на ідеях з проєкту:
https://github.com/wdlctc/recurrent_maskable

## Структура проєкту

```text
Chapter4/
├── Chapter4.1/
│   ├── CpSatSolution.py                 # CP-SAT оптимізація для згенерованого набору замовлень
│   └── CpSatSolutionBatch.py            # CP-SAT оптимізація пакетами
├── Chapter4.2/
│   ├── PPOTraining.py                   # Базове PPO-навчання
│   ├── MaskablePPOTraining.py           # PPO з маскуванням недопустимих дій
│   ├── RecurrentPPOTraining.py          # PPO з LSTM-політикою
│   ├── RecurrentMaskablePPOTraining.py  # PPO з LSTM та маскуванням дій
│   ├── ReinforcementLearningEnvironmentOptimized.py
│   └── MaskableRecurentPPO/             # Локальна реалізація recurrent-maskable PPO
├── Common/
│   ├── GantChartVisualizer.py           # Побудова Gantt-діаграм
│   ├── InputGenerator.py                # Генерація вхідних даних
│   ├── ProblemDefinition.py             # Опис замовлень, операцій і машин
│   └── ProblemSolution.py               # Структура розв'язку
└── requirements.txt
```

## Підготовка середовища

Команди нижче потрібно виконувати з кореня репозиторію.

```bash
cd Chapter4
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для Windows PowerShell активація середовища має такий вигляд:

```powershell
cd Chapter4
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Приклад 1. CP-SAT оптимізація

Скрипт `CpSatSolution.py` генерує набір замовлень, будує CP-SAT модель,
мінімізує довжину розкладу та виводить знайдений розклад.

```bash
cd Chapter4
PYTHONPATH=. python Chapter4.1/CpSatSolution.py
```

Після успішного запуску в консолі з'являться:

- статистика CP-SAT моделі;
- кількість знайдених розв'язків;
- довжина розкладу;
- розподіл операцій за машинами;
- Gantt-діаграма.

## Приклад 2. CP-SAT оптимізація пакетами

Скрипт `CpSatSolutionBatch.py` розбиває множину замовлень на пакети та поступово
додає їх до розкладу.

```bash
cd Chapter4
PYTHONPATH=. python Chapter4.1/CpSatSolutionBatch.py
```

Цей приклад зручний для демонстрації того, як точний метод можна застосовувати
до більшої кількості замовлень без одночасного розв'язання всієї задачі.

## Приклад 3. Навчання Maskable PPO

Скрипт `MaskablePPOTraining.py` навчає агента, який отримує маску допустимих дій.
Це запобігає вибору операцій, які не можна виконати в поточному стані середовища.

```bash
cd Chapter4
PYTHONPATH=.:Chapter4.2 python Chapter4.2/MaskablePPOTraining.py
```

Під час запуску створюється директорія `tensorboard_logs/`, а навчена модель
зберігається у файл `flexible_job_shop_ppo_model_multi_input_masked_actions.zip`.

## Приклад 4. Навчання Recurrent PPO

Скрипт `RecurrentPPOTraining.py` використовує LSTM-політику, яка може враховувати
послідовність попередніх станів.

```bash
cd Chapter4
PYTHONPATH=.:Chapter4.2 python Chapter4.2/RecurrentPPOTraining.py
```

Навчена модель зберігається у файл
`flexible_job_shop_recurrent_ppo_model_multi_input.zip`.

## Приклад 5. Навчання Recurrent Maskable PPO

Скрипт `RecurrentMaskablePPOTraining.py` поєднує LSTM-політику з маскуванням
недопустимих дій.

```bash
cd Chapter4
PYTHONPATH=.:Chapter4.2 python Chapter4.2/RecurrentMaskablePPOTraining.py
```

Цей варіант є найскладнішим серед наведених прикладів і потребує більше часу на
навчання, оскільки за замовчуванням використовує `500_000` кроків.

## TensorBoard

Для перегляду метрик навчання запустіть TensorBoard з директорії `Chapter4`:

```bash
tensorboard --logdir tensorboard_logs
```

Після запуску відкрийте адресу:

http://localhost:6006/

Типова структура логів:

```text
tensorboard_logs/
└── 30/
    ├── baseline/
    ├── masked/
    └── recurrent/
```

## Запуск з PyCharm

1. Відкрийте у PyCharm кореневу папку репозиторію.
2. Створіть або виберіть Python-інтерпретатор для `Chapter4/.venv`.
3. У конфігурації запуску встановіть робочу директорію `Chapter4`.
4. Додайте до `PYTHONPATH` значення `.` для CP-SAT прикладів або
   `.:Chapter4.2` для RL-прикладів.
5. Запустіть потрібний файл з `Chapter4.1` або `Chapter4.2`.

## Примітки для використання прикладів у книзі

- `Chapter4.1` демонструє математичне моделювання FJSP через обмеження CP-SAT.
- `Chapter4.2` демонструє формулювання тієї самої прикладної області як RL-середовища.
- Для швидких демонстрацій у книзі можна зменшити параметр `steps` у training-файлах.
- Для відтворюваності експериментів варто явно фіксувати seed у генераторі даних,
  середовищі та алгоритмі навчання.
