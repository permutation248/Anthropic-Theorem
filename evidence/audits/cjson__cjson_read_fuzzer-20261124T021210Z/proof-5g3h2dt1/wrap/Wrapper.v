(* written by oft check; never supplied by a pull request *)
From Stdlib Require Import QArith.
Require OSSVerify.cjson.cjson_read_fuzzer.Statements.
Require OSSVerify.Proofs.cjson.cjson_read_fuzzer.asan_ubsan_agrees.Proof.
Definition certified : OSSVerify.cjson.cjson_read_fuzzer.Statements.asan_ubsan_agrees := OSSVerify.Proofs.cjson.cjson_read_fuzzer.asan_ubsan_agrees.Proof.asan_ubsan_agrees_holds.
Set Printing Fully Qualified.
Redirect "assumptions" Print Assumptions certified.
