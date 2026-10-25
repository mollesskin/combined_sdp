# Minimal source changes

Original benchmark source and all prior files are untouched. `variants/V0/TokenBank.sol` is a byte-identical copy; hashes are in source_manifest.json.

V1 replaces only the annotated ignored call with capture of bool callSucceeded and require(callSucceeded).
V2 leaves the original low-level call intact and checks its return-data size is exactly 32, then copies that word to scratch memory and requires exactly 1. It does not check EVM success or introduce a high-level call. Full-word validation rejects noncanonical booleans; length validation precedes copying. It writes no storage, adds no public ABI, and uses memory at the free-memory pointer only transiently, after the external call and before function return.
V3 uses V1's check followed by the identical V2 decoder. Same compiler, call arguments and default low-level gas forwarding; checks consume different amounts of gas, so exact gas consumption is descriptive, not held identical. Transaction gas budget is held identical and comfortably exceeds these checks; no claim of behavior across all possible near-out-of-gas budgets.

No fixes to shadowed owner variables, public initializer, Ether withdrawal, deposit threshold or holder logic. Their existence is a limitation, not part of the treatment. InitTokenBank is invoked by the same deployer so original Ownable owner authorization is not altered. The actual studied entry is WitdrawTokenToHolder, not the direct WithdrawToken-only path of the earlier fixture.

Each V1–V3 unified diff is saved under variants/. All four are compiled with native 0.4.19; the runner compares canonical full ABI JSON, including inherited functions, against V0. ABI equality is interface evidence only. Behavioral comparability is limited to the defined normal probe/S1 and matched negative scenarios.

The new BehaviorToken is explicitly synthetic, not a replacement benchmark. Its only modes are normal true, false/no-transfer and empty revert/no-transfer. It has an always-zero allowance mapping to record the absence of transferFrom approval requirements. No unusual return/revert payload or extra test has been introduced.
