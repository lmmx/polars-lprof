import ".just/commit.just"
import ".just/ship.just"
import ".just/test.just"

pc-fix:
  prek run --all-files

[working-directory: "example"]
demo:
  ./run_plprof.sh

[working-directory: "example"]
demo-multi:
  ./run_plprof_multi.sh
