# Model Output FAQ

## Where are the tested model outputs?

Link each exact verbatim output and the user's named golden in the result
message itself, even when the report already links them. Label the mode,
request index, and actual token count. Do not substitute logs, hashes, or
a directory for the raw text. If a case did not produce text, say why.

## Do the modes match, and is the problem fixed?

Report these independently: exact text equality to the named golden,
token-ID equality when observed, and same-host offload equivalence to the
original frozen no-offload output. Give the first difference and a short
verbatim example. Identify retokenized IDs as inferred. A request that uses
its token budget inside an unclosed thinking section is not a completed
answer. Do not infer cross-host correctness from a same-host pass or claim a
code fix without a demonstrated defect and verification against the frozen
reference.