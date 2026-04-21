# ЛАБОРАТОРНАЯ РАБОТА № 3
**Паттерн проектирования:** Состояние (State)  
**Дисциплина:** Объектно-ориентированный анализ и проектирование (ООАП)  
**Приложение:** HR Tool — система управления персоналом  
**Реализация:** Python Flask + C# WinForms GUI demo  

## 1. Описание проблемы

В системе управления персоналом HR Tool каждый сотрудник находится в определённом жизненном состоянии. Для данного проекта используется следующий набор состояний:

* `Candidate` — кандидат, созданный вручную или полученный через клонирование шаблона сотрудника;
* `Active` — активный сотрудник, учитываемый в фонде зарплат и активной численности;
* `OnLeave` — сотрудник в отпуске или временно недоступный, но всё ещё находящийся в рабочем процессе;
* `Fired` — уволенный сотрудник, терминальное бизнес-состояние.

На первый взгляд состояние сотрудника можно хранить обычной строкой `status`. Однако в реальном приложении состояние влияет не только на отображаемый текст, но и на поведение объекта:

* какие переходы разрешены из текущего состояния;
* участвует ли сотрудник в расчёте фонда зарплат;
* входит ли сотрудник в активную численность;
* какие кнопки переходов должны быть доступны в интерфейсе;
* какие данные возвращаются в API для построения Kanban pipeline.

Таким образом, проблема заключается не в хранении значения `status`, а в управлении поведением, которое меняется в зависимости от текущего состояния сотрудника.

### 1.1 Реализация без паттерна

До применения паттерна поведение можно было реализовать через словарь допустимых переходов и проверки внутри класса `Employee`:

```python
VALID_TRANSITIONS = {
    "Candidate": ["Active", "Fired"],
    "Active":    ["OnLeave", "Fired"],
    "OnLeave":   ["Active", "Fired"],
    "Fired":     [],
}

class Employee:
    def can_transition_to(self, new_status: str) -> bool:
        return new_status in VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status: str):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition '{self.status}' -> '{new_status}'"
            )
        self.status = new_status

    def get_salary_fund(self):
        return self.salary if self.status != "Fired" else 0.0

    def get_employee_count(self):
        return 1 if self.status != "Fired" else 0
```

Такой подход работает для небольшого количества состояний, но быстро приводит к проблемам:

* правила переходов отделены от поведения конкретного состояния;
* при добавлении нового состояния нужно менять общий словарь и несколько методов;
* логика расчёта зарплаты и численности зависит от строковых проверок;
* интерфейс вынужден ориентироваться на строковые значения и внешние правила;
* класс `Employee` начинает отвечать сразу за слишком много решений.

Если добавить, например, состояние `Probation`, потребуется изменить переходы, расчёт метрик, UI-кнопки и API-ответы. Это нарушает принцип открытости/закрытости: система должна быть открыта для расширения, но закрыта для изменения существующего кода.

## 2. Решение: применение паттерна Состояние

Паттерн Состояние (State) позволяет вынести поведение, зависящее от состояния, в отдельные классы. Объект-контекст (`Employee`) хранит ссылку на объект состояния (`EmployeeState`) и делегирует ему операции.

В результате состояние перестаёт быть просто строкой. Оно становится полноценным объектом, который знает:

* какие переходы из него разрешены;
* как выполнить переход;
* как это состояние влияет на фонд зарплат;
* как оно влияет на подсчёт активных сотрудников;
* какие метаданные нужны интерфейсу.

### 2.1 Участники паттерна

В проекте участники паттерна распределены следующим образом:

| Роль в паттерне State | Класс в проекте | Назначение |
| --- | --- | --- |
| `Context` | `Employee` | Сотрудник, поведение которого зависит от текущего состояния |
| `State` | `EmployeeState` | Абстрактное состояние с общим интерфейсом |
| `ConcreteState` | `CandidateState` | Состояние кандидата |
| `ConcreteState` | `ActiveState` | Состояние активного сотрудника |
| `ConcreteState` | `OnLeaveState` | Состояние сотрудника в отпуске |
| `ConcreteState` | `FiredState` | Терминальное состояние уволенного сотрудника |

Основная Python-реализация находится в файлах:

* `models/employee.py`
* `models/employee_state.py`
* `app.py`

Дополнительно создана C# WinForms GUI-версия для демонстрации того же жизненного цикла сотрудника:

* `HrStateWinForms/Employee.cs`
* `HrStateWinForms/EmployeeState.cs`
* `HrStateWinForms/MainForm.cs`

## 3. Реализация паттерна в Python

### 3.1 Абстрактное состояние — EmployeeState

Базовый класс `EmployeeState` определяет общий интерфейс для всех состояний:

```python
class EmployeeState:
    name = "Unknown"
    label = "Unknown"
    color = "#1a1a2e"
    bg = "rgba(26,26,46,.08)"

    def available_transitions(self) -> list[str]:
        return []

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.available_transitions()

    def transition_to(self, employee: "Employee", new_status: str):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition '{self.name}' -> '{new_status}'"
            )
        employee.set_state(state_from_name(new_status))

    def get_salary_fund(self, employee: "Employee") -> float:
        return employee.salary

    def get_employee_count(self, employee: "Employee") -> int:
        return 1
```

Здесь определено поведение по умолчанию: сотрудник учитывается в фонде зарплат и численности, а список переходов пустой. Конкретные состояния переопределяют только то, что отличается.

### 3.2 Конкретное состояние — CandidateState

Кандидат может быть принят на работу или отклонён:

```python
class CandidateState(EmployeeState):
    name = "Candidate"
    label = "Candidate"

    def available_transitions(self) -> list[str]:
        return ["Active", "Fired"]
```

Состояние `Candidate` является начальным для нового сотрудника и для клонированного сотрудника-шаблона. Это хорошо сочетается с ранее реализованным паттерном Prototype: `Employee.clone()` создаёт нового сотрудника со статусом `Candidate`.

### 3.3 Конкретное состояние — ActiveState

Активный сотрудник может уйти в отпуск или быть уволен:

```python
class ActiveState(EmployeeState):
    name = "Active"
    label = "Active"

    def available_transitions(self) -> list[str]:
        return ["OnLeave", "Fired"]
```

Для состояния `Active` используется поведение по умолчанию:

* сотрудник участвует в фонде зарплат;
* сотрудник входит в активную численность;
* API возвращает доступные переходы `OnLeave` и `Fired`.

### 3.4 Конкретное состояние — OnLeaveState

Сотрудник в отпуске может вернуться к работе или быть уволен:

```python
class OnLeaveState(EmployeeState):
    name = "OnLeave"
    label = "On Leave"

    def available_transitions(self) -> list[str]:
        return ["Active", "Fired"]
```

В данном проекте `OnLeave` остаётся частью жизненного цикла сотрудника. Это не терминальное состояние, поэтому из него есть два перехода.

### 3.5 Конкретное состояние — FiredState

Состояние `Fired` является терминальным бизнес-состоянием. Из него нет доступных переходов, а сотрудник больше не участвует в расчётах:

```python
class FiredState(EmployeeState):
    name = "Fired"
    label = "Fired"

    def get_salary_fund(self, employee: "Employee") -> float:
        return 0.0

    def get_employee_count(self, employee: "Employee") -> int:
        return 0
```

Именно здесь видна польза паттерна: правило `salary fund = 0` больше не проверяется через `if employee.status == "Fired"` в разных частях системы. Оно инкапсулировано в классе состояния.

## 4. Контекст — Employee

Класс `Employee` является контекстом паттерна State. Он хранит текущее состояние в поле `_state`:

```python
class Employee(OrgComponent):
    def __init__(self, emp_id, name, position, salary,
                 status="Candidate", department_id=None):
        self.id = emp_id
        self.name = name
        self.position = position
        self.salary = float(salary)
        self.department_id = department_id
        self._state = state_from_name(status)
```

Снаружи объект всё ещё выглядит удобно: у него есть свойство `status`, которое возвращает имя текущего состояния:

```python
@property
def status(self) -> str:
    return self._state.name
```

Но реальные действия делегируются объекту состояния:

```python
def transition_to(self, new_status: str):
    self._state.transition_to(self, new_status)

def available_transitions(self) -> list[str]:
    return self._state.available_transitions()

def get_salary_fund(self):
    return self._state.get_salary_fund(self)

def get_employee_count(self):
    return self._state.get_employee_count(self)
```

Таким образом, `Employee` не содержит длинных цепочек `if/elif`. Он не знает деталей каждого состояния, а только делегирует работу текущему объекту `EmployeeState`.

## 5. Интеграция с Flask API

Паттерн State используется в маршруте перехода сотрудника:

```python
@app.route("/api/employees/<int:emp_id>/transition", methods=["POST"])
def transition_employee(emp_id):
    emp = find_emp(emp_id)
    if not emp:
        return jsonify({"error": "Not found"}), 404

    body = request.get_json(silent=True) or {}
    new_status = body.get("status")

    try:
        emp.transition_to(new_status)
        return jsonify(emp.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
```

Контроллер не проверяет самостоятельно, можно ли выполнить переход. Он вызывает `emp.transition_to(new_status)`, а дальше решение принимает текущее состояние сотрудника.

Также State pattern влияет на ответы API:

```python
def to_dict(self):
    return {
        "status": self.status,
        "statusLabel": meta["label"],
        "employeeCount": self.get_employee_count(),
        "salaryFund": self.get_salary_fund(),
        "transitions": self.available_transitions(),
    }
```

Поле `transitions` используется интерфейсом для построения кнопок доступных переходов. Если сотрудник находится в `Fired`, список переходов пустой.

## 6. Интеграция с GUI

В проекте есть два интерфейса:

* веб-интерфейс Flask (`templates/index.html`);
* отдельное C# WinForms приложение (`HrStateWinForms`).

### 6.1 Web UI

В Flask-интерфейсе пользователь выбирает сотрудника, видит его текущий статус и доступные переходы. Кнопки переходов строятся на основе поля `transitions`, которое приходит из API:

```javascript
const transBtns = (emp.transitions || []).map(t => {
  const map = {
    'Active': emp.status === 'OnLeave'
      ? `<button onclick="doTransition(${emp.id},'Active')">Return</button>`
      : `<button onclick="doTransition(${emp.id},'Active')">Hire</button>`,
    'OnLeave': `<button onclick="doTransition(${emp.id},'OnLeave')">Send on Leave</button>`,
    'Fired': `<button onclick="doTransition(${emp.id},'Fired')">Terminate</button>`,
  };
  return map[t] || '';
}).join('');
```

Важно, что интерфейс не решает, какие переходы допустимы. Он только отображает то, что разрешило текущее состояние.

### 6.2 C# WinForms GUI

C# приложение реализует ту же модель для демонстрации паттерна в desktop GUI. В файле `HrStateWinForms/EmployeeState.cs` определён абстрактный класс:

```csharp
public abstract class EmployeeState
{
    public abstract string Name { get; }
    public abstract string Label { get; }
    public virtual IReadOnlyList<string> AllowedTransitions => Array.Empty<string>();

    public virtual decimal GetSalaryContribution(Employee employee) => employee.Salary;
    public virtual int GetEmployeeContribution(Employee employee) => 1;

    public void Transition(Employee employee, string newState)
    {
        if (!AllowedTransitions.Contains(newState))
        {
            throw new InvalidOperationException(
                $"Cannot transition '{Name}' -> '{newState}'.");
        }

        employee.SetState(Create(newState));
    }
}
```

GUI показывает:

* карточки метрик по состояниям;
* список сотрудников;
* текущий state сотрудника;
* доступные и заблокированные переходы;
* журнал переходов.

Это делает применение паттерна визуально очевидным: при изменении состояния меняются доступные кнопки, метрики и поведение объекта.

## 7. Взаимодействие с другими паттернами проекта

Данная лабораторная работа не изолирована от предыдущих частей проекта. В HR Tool уже используются паттерны Prototype и Composite, а State дополняет их.

### 7.1 Prototype + State

Метод `Employee.clone()` создаёт нового сотрудника на основе существующего, но всегда сбрасывает состояние в `Candidate`:

```python
def clone(self):
    return Employee(
        emp_id=None,
        name=self.name + " (copy)",
        position=self.position,
        salary=self.salary,
        status="Candidate",
        department_id=self.department_id,
    )
```

Это означает, что клонированный сотрудник является шаблоном для нового найма. Далее его жизненный цикл управляется паттерном State.

### 7.2 Composite + State

Класс `Department` считает фонд зарплат и количество сотрудников через единый интерфейс `OrgComponent`:

```python
def get_salary_fund(self):
    return sum(c.get_salary_fund() for c in self._children)

def get_employee_count(self):
    return sum(c.get_employee_count() for c in self._children)
```

Если дочерний элемент является сотрудником, он сам делегирует расчёт своему текущему состоянию. Например, `FiredState` возвращает `0` для зарплатного фонда и численности. Таким образом, Composite обходит дерево, а State определяет поведение листовых узлов.

## 8. Диаграммы

Для паттерна State требуется подготовить две UML-диаграммы:

* диаграмму классов;
* диаграмму состояний.

В папке `docs` подготовлены вспомогательные материалы:

* `docs/pure-uml-state-pattern-guide.md` — руководство для ручного построения pure UML;
* `docs/state-pattern-class.mmd` — Mermaid-черновик диаграммы классов;
* `docs/employee-lifecycle-state.mmd` — Mermaid-черновик диаграммы состояний;
* `docs/state-pattern-class.puml` — PlantUML-черновик диаграммы классов;
* `docs/employee-lifecycle-state.puml` — PlantUML-черновик диаграммы состояний.

Важно: согласно требованиям преподавателя, итоговые диаграммы должны быть нарисованы вручную или в визуальном UML-редакторе. Mermaid и PlantUML можно использовать только как черновик.

### 8.1 Диаграмма классов

На диаграмме классов необходимо показать:

* `Employee` как контекст;
* `EmployeeState` как абстрактное состояние;
* `CandidateState`, `ActiveState`, `OnLeaveState`, `FiredState` как конкретные состояния;
* связь `Employee --> EmployeeState` как текущий state;
* наследование конкретных состояний от `EmployeeState`;
* зависимость `EmployeeState ..> Employee`, так как состояние изменяет контекст через `employee.set_state(...)`;
* опционально `AppController`, который вызывает операции сотрудника.

Важно не использовать композицию между `Employee` и `EmployeeState`, потому что состояние может заменяться в процессе работы. Более корректно показать направленную ассоциацию.

### 8.2 Диаграмма состояний

Диаграмма состояний должна описывать жизненный цикл одного объекта — `Employee`.

Переходы:

| Из состояния | В состояние | Событие |
| --- | --- | --- |
| Initial | `Candidate` | `createEmployee() / setState(Candidate)` |
| `Candidate` | `Active` | `hire()` |
| `Candidate` | `Fired` | `reject()` |
| `Active` | `OnLeave` | `sendOnLeave()` |
| `Active` | `Fired` | `terminate()` |
| `OnLeave` | `Active` | `returnFromLeave()` |
| `OnLeave` | `Fired` | `terminate()` |

Состояние `Fired` не имеет исходящих переходов. Это терминальное бизнес-состояние: сотрудник остаётся в системе, но больше не участвует в фонде зарплат и активной численности.

## 9. Сравнение подходов

| Критерий | Без паттерна | С паттерном State |
| --- | --- | --- |
| **Переходы между статусами** | Общий словарь или цепочка `if/elif` | Каждое состояние само определяет доступные переходы |
| **Расчёт зарплатного фонда** | Проверка `if status == "Fired"` в разных местах | `FiredState.get_salary_fund()` возвращает `0` |
| **Расчёт численности** | Проверка статуса внутри `Employee` или контроллера | `get_employee_count()` делегируется текущему состоянию |
| **Расширяемость** | Добавление состояния требует изменения существующего кода | Добавляется новый класс состояния |
| **Связность кода** | `Employee` знает все правила всех состояний | `Employee` работает только с интерфейсом `EmployeeState` |
| **GUI** | Интерфейс сам должен знать правила переходов | Интерфейс отображает список `transitions` из модели |
| **Тестируемость** | Сложно тестировать отдельные правила | Каждое состояние можно тестировать отдельно |

## 10. Запуск проекта

### 10.1 Python Flask

```powershell
cd C:\Users\umut0\Desktop\lab1_prototype
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

После запуска открыть:

```text
http://127.0.0.1:5000
```

### 10.2 C# WinForms

```powershell
cd C:\Users\umut0\Desktop\lab1_prototype\HrStateWinForms
$env:DOTNET_CLI_HOME='C:\Users\umut0\Desktop\lab1_prototype\.dotnet-home'
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1'
dotnet run
```

## 11. Проверка корректности

Проверены следующие сценарии:

* создание нового сотрудника создаёт состояние `Candidate`;
* `Candidate -> Active` выполняется успешно;
* `Active -> OnLeave` выполняется успешно;
* `OnLeave -> Active` выполняется успешно;
* `Active -> Fired` выполняется успешно;
* `OnLeave -> Fired` выполняется успешно;
* переход из `Fired` в другое состояние запрещён;
* `FiredState` возвращает `0` для фонда зарплат;
* `FiredState` возвращает `0` для активной численности;
* клонирование сотрудника создаёт нового сотрудника в состоянии `Candidate`;
* клонирование отдела рекурсивно создаёт сотрудников-шаблоны;
* Kanban pipeline строится на основе текущих состояний сотрудников.

## 12. Вывод

Применение паттерна Состояние в HR Tool позволило заменить строковые проверки и централизованные таблицы переходов на объектно-ориентированную модель жизненного цикла сотрудника.

Основной результат: поведение сотрудника теперь зависит от объекта состояния, а не от набора `if/elif` в классе `Employee` или контроллере Flask.

Паттерн дал следующие улучшения:

* **Инкапсуляция правил переходов:** каждое состояние само определяет, куда из него можно перейти.
* **Снижение связанности:** `Employee` не знает всех правил конкретных состояний.
* **Расширяемость:** новое состояние можно добавить отдельным классом.
* **Улучшение GUI:** интерфейс получает готовый список допустимых переходов и не дублирует бизнес-логику.
* **Корректные бизнес-метрики:** состояние `Fired` само определяет, что сотрудник не участвует в зарплатном фонде и активной численности.
* **Совместимость с Prototype и Composite:** клонирование создаёт кандидатов, а дерево отделов корректно считает зарплату и численность через состояние сотрудников.

Таким образом, паттерн State подходит для данной предметной области естественно: HR-система действительно работает с жизненным циклом сотрудника, где каждый статус имеет собственные правила и влияет на поведение приложения.
