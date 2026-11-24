(* Authored environment smoke check; this is not a theorem from the research report. *)
From Stdlib Require Import ZArith.
From LinuxProcessSemantics.LinuxProcessSem Require Import State.
Check State.ProcInput.
Check State.event.
Example linux_page_size_is_4096 : State.page_size = 4096%Z.
Proof.
  reflexivity.
Qed.
