# Протокол пилота reentrancy, версия 1

Протокол зафиксирован до первого запуска анализаторов. Это целевая пилотная выборка, а не случайная или репрезентативная выборка всего датасета. Запрещено менять состав по результатам Slither/Mythril.

Критерии включения: файл в dataset/reentrancy; разметка reentrancy в vulnerabilities.json; самостоятельный контракт без импортов и наследования; не более 60 строк; Solidity 0.4.x с версией из versions.csv; доступная payable-функция пополнения учёта; внешний ETH-вызов до окончательного обновления учёта; проверка неудачи вызова с откатом. Дополнительно требуется ручная проверка локального преобразования. Фиксированная квота пилота — три контракта: etherstore.sol, reentrancy_dao.sol, reentrancy_simple.sol. Остальные файлы вне пилота; inventory не утверждает, что каждый из них нарушает критерии. Расширение выборки требует новой версии протокола до анализа.

baseline — побайтовая копия. CEI переносит все связанные эффекты перед вызовом; reentrancy_simple сохраняет сумму в локальную переменную. Ошибка отправки откатывает эффекты. Guard — собственный совместимый с Solidity 0.4 mutex с require и сбросом после тела; это не импорт современной OpenZeppelin. В пилоте защищён единственный вход вывода; функции пополнения не вызывают внешний код. Комбинация применяет оба преобразования. ABI функций сохраняется. Варианты сохраняют исходные комментарии/лицензии; старые @vulnerable_at_lines относятся исключительно к baseline. Новые номера строк не являются ground truth.

## Воспроизведение

1. `python3 experiments/reentrancy/prepare.py`
2. Подготовить отдельное окружение Python с совместимыми Slither/Mythril и зависимостями. Поместить исполняемые нативные solc точных версий из manifest.json в `experiments/reentrancy/toolchain/solc-VERSION`. Не менять pragma.
3. В этом окружении выполнить `python experiments/reentrancy/run.py --lock`. Скрипт фиксирует фактически установленные версии, pip freeze, хеши исполняемых файлов, платформу. Lock создаётся однократно; сохранить его вместе с результатами. До этого шага toolchain не считается зафиксированным.
4. `python experiments/reentrancy/run.py` — последовательные 24 запуска (3 × 4 × 2), отдельная директория на каждый запуск. При изменении окружения анализ запрещён. Использовать то же окружение и машину, без конкурирующих нагрузок.

Для одного исходника все варианты используют один solc; между исходниками версии различаются согласно versions.csv. Оптимизатор не включается. Slither запускает полный набор детекторов; Mythril: 3 транзакции, 120 секунд символического исполнения, 10000 мс solver timeout; внешний предел обоих — 180 секунд. Лимиты памяти/CPU средствами ОС не установлены; сравнение времени между разными машинами невалидно. Это локальный harness, не герметичный контейнер: для публикации требуется архив окружения/образ с digest и фиксация всех транзитивных зависимостей, включая solver.

Каждый запуск сохраняет UTC, команду, cwd, исходный SHA-256, длительность, exit code, stdout/stderr и сырой JSON. Неудачная компиляция, отсутствие инструментов, таймаут и отсутствие находок различаются. Mythril может вернуть частичный результат после внутреннего таймаута; report_success не означает полноту исследования. Отсутствие предупреждений не доказывает безопасность. Для оценки исправлений отдельно нужны компиляция и поведенческие тесты: обычный вывод, повторный вход, отказ получателя, повторный вывод после успешной операции. Они пока не выполнены.

## Форматы команд

Параметры проверены по первичным источникам:
- Slither: https://github.com/crytic/slither/wiki/Usage
- Mythril: https://github.com/ConsenSysDiligence/mythril/blob/develop/mythril/interfaces/cli.py

## Текущее состояние

Исходники и варианты подготовлены. В исходном окружении отсутствуют Slither, Mythril и solc. Анализ, проверка компиляции и доказательство поведенческой эквивалентности не выполнены. Запись preflight в runs фиксирует эту блокировку; она не является результатом анализа.

# Protocol v2 — frozen before compilation and analysis

This extension implements the expanded research request. The v1 three-contract purposive pilot and all 12 Solidity files remain unchanged. No tool findings were available at selection time. The original criteria preceded the earlier transformations; this extension documents that history rather than claiming a new prospective selection. Dataset: SmartBugs Curated, repository commit 230e649123477eff332742a59a1c7cc6dc286cab.

## Sampling rule and exclusions

The fixed whitelist is etherstore.sol (R01), reentrancy_dao.sol (R02), reentrancy_simple.sol (R03). All must be annotated reentrancy, standalone without imports/inheritance, at most 60 physical lines, Solidity 0.4.x, with payable funding and a reverting failure path for the external ETH withdrawal. Selection is a purposive pilot, not a random draw. The inherited whitelist is an explicit final sampling restriction. Exclusions are recorded per source in selection.csv. Failed compilation/analysis must never cause replacement or removal.

## Treatments and behavior

V0=baseline, V1=CEI, V2=mutex, V3=CEI+mutex. Source filenames and ABI function signatures remain unchanged. CEI moves withdrawal effects before interaction; the simple balance withdrawal uses a local amount snapshot. Mutex adds private storage and a modifier on the sole withdrawal entry point. It uses legacy-compatible Solidity, not a newer OpenZeppelin dependency. Changes to callback-visible state, gas consumption, storage layout and nested-withdrawal behavior are inherent treatments. ABI equality is checked after compilation. This does not establish full semantic equivalence, and does not test proxy storage compatibility or read-only reentrancy.

## Execution and missingness

settings.json freezes limits, order and flags. Compile each of 12 sources independently using the exact compiler in versions.csv, no optimization, --combined-json abi,bin. Retain nonzero compiler exits and raw outputs. Do not upgrade Solidity to make tools succeed. Run Slither against every successfully compiled variant, regardless of findings in other variants. Record skipped analysis for compilation errors or unavailable tools. Mythril is optional, in a separate environment; enable it for the whole sample only if its version probe succeeds before sample analysis. No fallback tool or detector configuration selected in response to sample findings. Compiler/tool compatibility failure is an experimental outcome, not a reason to change selection or version.

The environment lock records runtime versions, package inventories, executable hashes, settings hash and runner/source hashes. Every run snapshots these inputs and appends UTC command start/end events. Protocol v2 deliberately makes Mythril optional (v1 required both tools), adds a separate compilation phase and CSV results, and preserves all earlier logs. Dependency download failures, native execution compatibility and CA-certificate setup issues are deviations logged in setup and run events. No Ethereum RPC or deployed contract interaction is permitted.

## Measurement plan

One CSV row per contract × variant × tool (including optional-tool skips). Count a Slither finding as one entry in results.detectors; all entries are detector findings, including informational/optimization notices, not confirmed exploitable vulnerabilities. Reentrancy finding count includes check IDs beginning reentrancy-. vulnerability_detected is the boolean presence of any detector finding. A Mythril finding is an issues entry, reentrancy is SWC-107. Unknown/unavailable counts are empty CSV cells, never zero. JSON success alone is insufficient: timeout, malformed report and failed process statuses remain explicit. Internal Mythril budget termination may produce partial results; all successful Mythril records are budget-limited, not exhaustive proofs.

Primary comparison: paired reentrancy finding counts and detection presence for V1,V2,V3 relative to V0 within the same source and tool, restricted to completed valid reports; disclose denominators and all missing cases. V3 versus V1/V2 assesses additional detector-observed reduction. No statistical power, broad effectiveness, exploit prevention or combination superiority claim is justified by three pilot cases or static finding counts alone. Dynamic exploit and regression tests are future work; no behavioral test outcomes will be fabricated.

# Protocol v3 — deterministic Mythril compiler selection

The completed v2 run `20261022T084546.259653Z` is retained as a diagnostic batch. Inspection of installed Mythril source showed that SOLC alone does not unconditionally override pragma-based compiler selection. In that restricted environment the compiler registry was empty, allowing the SOLC fallback; this is insufficient for portable reproducibility. V3 explicitly passes --solv VERSION and pre-registers the SHA256-verified native compilers under isolated SOLCX_BINARY_PATH/solc-vVERSION. The runner verifies registered binary hashes at preflight. No compiler upgrade, source/sample change, detector change, budget change or result-dependent exclusion is allowed. V3 is a complete repeated batch; do not pool it with v2 as independent samples. V2 environment lock is retained in setup/environment.v2.lock.json.

Mythril/py-solc-x may reject compiler 0.4.10 before analysis, since the installed py-solc-x supports versions >=0.4.11. Such errors must remain unknown-count analysis failures for all affected variants, even though standalone compilation succeeds. No compatibility workaround using a newer compiler is permitted. The v3 environment lock is the published default. Preflight version probes allow 90 seconds for first-start cache initialization; this does not alter the analysis budgets.
