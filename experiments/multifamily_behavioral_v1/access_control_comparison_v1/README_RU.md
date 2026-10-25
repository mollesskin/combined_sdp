# Access-control партия: выполненные результаты

AI-assisted локальная исследовательская реализация. Утверждённый RQ и многокатегорийный план сохранены. Это не текст сдаваемого assignment. Arithmetic не запускалась и не изменялась; read-only аудит всех 1760 файлов и hashes прошёл. DoS не запускалась и остаётся следующим этапом.

## Охват и выполненные проверки

Рассмотрены **16 из 16** access-control файлов из сохранённого pinned baseline test-results.json. Завершены:

- **2 полных V0/V1/V2/V3 сравнения:** arbitrary_location_write_simple и wallet_04_confused_sign.
- **12 single-fix сравнений V0/F1:** три incorrect_constructor_name, mapping_write, multiowned_vulnerable, mycontract, parity_wallet_bug_2, phishable, simple_suicide, unprotected0, wallet_02_refund_nosub, wallet_03_wrong_constructor. Они не учитываются как комбинационные сравнения.
- **2 нерешённых случая:** FibonacciBalance и proxy; сохранены их V0, исходные hashes, разбор и причины. Оба V0 скомпилированы, сравнительные исполнения/метрики N/A.

Сохранены 34 source variants; исполнялись 32. Вместе с fixture-файлом скомпилированы 35 Solidity source files. Во всех вариантах фактически выбран **solc 0.4.25**, optimizer enabled/runs=200; local Hardhat hardfork **Shanghai**, без fork внешней сети. Новые проекты используют ту же compiler matrix и network settings; единственное изменение config — reporter, точный diff сохранён. Node v20.20.0, npm 10.8.2, Hardhat 2.22.5; зависимости не обновлялись.

Есть 47 уникальных case×scenario; 110 variant×scenario instances на один запуск. Каждый сценарий начинается с hardhat_reset, нового deploy и одинаковых внешних условий. На каждый итоговый запуск: **266 наблюдений**, в том числе 258 измеряемых транзакций и 8 отдельных проверок owner при deployment. Deploy/setup-транзакции сохраняются как evidence, но не прибавляются к этим 258. Два итоговых запуска дали 532 наблюдения; это повторы, а не дополнительные исходные контракты.

По указанной в обзоре AC_INIT_CLONE три Missing-файла образуют одну группу. Всего 14 групп, из них 12 исполнялись: 2 factorial groups и 10 single-fix groups. Singleton здесь не доказывает независимость. Пофайловые и групповые результаты сохранены раздельно в file_summary.csv/group_summary.csv.

## V3 против A и против B

| Сравнение | Защитные требования | Разрешённая функциональность | Общий oracle по вызовам |
|---|---|---|---|
| V3 против V1/A | 8 равенств, 0 улучшений/ухудшений | 14 равенств, 0 улучшений/ухудшений | 22 равенства |
| V3 против V2/B | 8 равенств, 0 улучшений/ухудшений | 12 равенств и 2 улучшения, 0 ухудшений | 20 равенств и 2 улучшения |

У arbitrary_location_write_simple A, B и A+B прошли все 9 наблюдений. Оба механизма закрывают одно no-underflow свойство: pre-guard непустоты и checked subtraction с post-result проверкой. Это перекрывающиеся механизмы, а не два независимых класса угроз.

У wallet_04 V1 и V3 прошли все 13 наблюдений. V2 прошёл 11/13: исходный ошибочный `>=`, намеренно сохранённый в B, отклоняет нулевое и частичное снятие при ненулевом credit. Это один унаследованный функциональный дефект, наблюдаемый в двух вызовах, а не две уязвимости. V0 также отклоняет эти вызовы. V3 восстанавливает допустимый домен благодаря A; дополнительного защитного эффекта сочетания против A или B в проверенных сценариях **не обнаружено**. Новых функциональных регрессий от добавления B к A не наблюдалось. Нельзя назвать B полностью сохраняющим разрешённую функциональность.

Gas сравнивался отдельно при совпадении inputs, before contract state и execution status. Для V3−A: 14 successful вызовов, delta от 0 до 135 gas; 8 reverted, delta 0. Для V3−B: 12 сопоставимых successful, delta от −2 до 0 gas; 8 reverted, delta от −7121 до 0 gas. Два функционально расходящихся вызова V3/B по gas не сравнивались. Разница раннего guard и позднего отката после transfer объясняет возможность меньших затрат на запрещённом вызове. Deployment gas и cost-effectiveness score не рассчитывались.

## Single-fix результаты и конкретные последствия

Все 12 F1 прошли общий oracle в выполненных сценариях: **54/54 разрешённых наблюдения** и **35/35 защитных наблюдений** (33 forbidden/no-effect и 2 must-revert). Это проверенный набор, не доказательство сохранения всей возможной функциональности.

- Constructor fixes назначают deployer owner/creator при deployment, удаляя ошибочный runtime initializer. Искусственный post-deploy workflow не вводился. Смена ABI/lifecycle раскрыта; для Missing вызов удалённого selector может успешно попасть в fallback, но права не меняет — это корректный no-effect.
- В mapping_write сохранён произвольный uint256 key domain; mapping не даёт array-индексу переписать owner. Owner остаётся нулевым: его init не исправлялся. Artificial funding 1 wei раскрыто; lawful owner withdrawal N/A. Mapping также меняет поведение отсутствующего key на zero, это семантическое расширение, не полная эквивалентность.
- Multiowned сохраняет выдачу/отзыв делегированных прав и разрешённые выплаты; посторонний не может сам себя назначить.
- tx.origin fixes разрешают прямой owner-вызов и предотвращают перенос полномочий через relay. Получателю не вводится allowlist.
- Parity оценён только как прямо развёрнутый WalletLibrary, как в авторском тесте. Guard закрывает все три init entrypoints, existing only_uninitialized сохраняется. Proxy-compatible deployment authority/storage policy не решена и не заявляется проверенной.
- Для simple_suicide deployer authority явно выведена из роли owner в functional test, а не якобы присутствует в исходнике. Проверена no-argument сигнатура и удаление code в Shanghai. Это single экспериментальная lifecycle policy без второго искусственного механизма.
- Refund fix сохраняет право каждого вкладчика на возврат и атомарный откат при reverting recipient. Независимый математический claim ledger фиксирует у V0 две лишние выплаты по **6 wei** в отдельных точках одного сценария; они не трактуются как независимые уязвимости. У F1 избыточных выплат нет. У wallet_04 V0 forbidden withdraw 11 wei при credit 10 даёт excess 1 wei; без credit withdraw 1 wei также даёт excess 1 wei. В protected вариантах эти вызовы откатываются.

Защита не оценивается только по revert: сохранены successful harmless no-op вызовы, правильные отказы и состояние получателей с поправкой на transaction gas. Метрики адресов/credit/ETH и нарушения не складываются в PES или универсальную шкалу.

## Нерешённые требования

**FibonacciBalance:** исходник явно разрешает fallback library calls, но shared storage layout позволяет менять library pointer. До architecture comparison нужны точные разрешённые selector/setStart semantics и модель правильной Fibonacci-последовательности/выплат. Простой owner-only запрет уничтожит часть исходного workflow без обоснования.

**Proxy:** исходник и тест не определяют доверенное множество callee и делегированных пользователей. Benign метод того же атакующего fixture не обосновывает allowlist. Caller guard + target policy без этого были бы новыми требованиями, введёнными ради комбинации.

Эти два случая не заменялись другими и не превращались в нулевые показатели эффективности.

## Чистый повтор и воспроизведение

Итоговые `runs/run1` и `runs/run2` совпали по всем наблюдениям, точным inputs, состояниям, setup, receipts/errors и gas, за исключением новых raw output paths. Второй запуск выполнен после clean и повторной компиляции. **107 evidence checks passed**, infrastructure/setup/compilation errors итоговых запусков отсутствуют. Все reverted транзакции сохранили наблюдаемый rollback. Сами контрактные нарушения V0 и функциональные отказы V2 сохранены как данные, а не инфраструктурные ошибки.

Из корня репозитория:

```bash
bash experiments/multifamily_behavioral_v1/access_control_comparison_v1/reproduce.sh
```

Скрипт создаёт новый `runs/reproduction_<UTC>_<pid>`, дважды clean/compile/run в этом access-control project и выполняет analyze.py. Никогда не перезаписывает существующий output directory. Команда дополнительно выполнена успешно; новый путь сохранён в `reproduction_check.log`, её два запуска и validation.log — в указанном каталоге. Эти дополнительные повторы не увеличивают основной размер выборки.

Проверка уже сохранённых итогов:

```bash
python3 experiments/multifamily_behavioral_v1/access_control_comparison_v1/analyze.py
```

`project/node_modules` — ссылка на установленный baseline `stand_reproduction/20261023T024815Z_oJrMgr/project/node_modules`; для переноса нужен этот установленный набор. Reproduce не устанавливает пакеты, не вызывает публичные сети, arithmetic или DoS. Build generator запускается только из корня repo; обычное воспроизведение его не требует. Его повторное исполнение перегенерирует source/registry и требует обновить metadata нового исполнения.

## Проверяемые артефакты

- `PROTOCOL_RU.md`, `CASE_REVIEW_RU.md`, `registry.json`: permission models, baseline defects, existing mechanisms, targets и решения по каждому файлу.
- `project/contracts/{V0,V1,V2,V3,F1}`, `diffs/`, `SHA256SUMS.json`: исходники, точные diffs/hashes. `ResearchDebit` — собственный AI-assisted helper, не оригинальная сторонняя библиотека.
- `project/measure.js`, `analyze.py`, `reproduce.sh`: test/measurement code, oracle, ledger и evidence checks.
- `runs/run1`, `runs/run2`: CSV/JSON, индивидуальные raw receipt/error/setup outputs, compiler settings, ABI comparisons, scenario manifests. ABI equality — только интерфейсная проверка; constructor изменения отражены отдельно.
- `compilation_manifest.json`: actual compiler/settings всех 34 сохранённых вариантов, включая unresolved V0.
- `summary.json`, `file_summary.csv`, `group_summary.csv`, `comparisons.csv`: файлы/группы и отдельные V3−A/V3−B.
- `inputs/`: неизменённые исходные review, author tests, saved report и baseline log. Рабочий baseline project/scripts/test-results.json отсутствовал при осмотре; исторический pinned report 195/91 и reproduction log 71/33 имеют разное происхождение и не выдаются за новые protected results.
- `frozen_before_first_run/`, `runs/initial_01`, `initial_01.log`, `ERRORS_RU.md`: исходный протокол/инструмент и полный предварительный прогон с исправленной затем ошибкой типа oracle. Ничего из него не заменено итоговыми файлами.
- `versions.txt`, `dependencies.json`, `config.diff`, `COMMANDS.md`, compile/run/validation logs: окружение, конфигурация и команды.
- `arithmetic_before.json`, `preservation_check.json`: read-only подтверждение сохранности предыдущей партии.

uint256, wei, arithmetic discrepancy и gas в итоговых measurement JSON/CSV — decimal strings; малые step/status/receipt metadata могут быть числовыми. N/A/null не заменяются нулями. Числовые нули там, где показатель применим, означают реальный нулевой результат. `contract_outflow_wei` — signed net decrease: при incoming deposit отрицателен, а не «отрицательная атака». `unauthorized_outflow_wei` применим только к forbidden финансовым вызовам. `excess_payout_wei` отделяет превышение credit/правильной выплаты от всей суммы forbidden transaction. Reverted before/after различаются у sender по gas в raw accounts; сравнение нормализует фактически уплаченный gas. Storage coverage раскрыта в observe(); это observed rollback, а не формальная проверка всего EVM state space.

Исследование ограничено этими сценариями, выбранными single-fix permission models и указанным локальным fork. Exhaustive/fuzz verification, полная эквивалентность и реконструкция всей исторической Parity proxy architecture не заявляются.
