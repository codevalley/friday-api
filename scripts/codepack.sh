npx repomix --include "configs/,domain/,metadata/,orm/,repositories/,routers/,schemas/,services/,utils/,dependencies.py,main.py,setup.py" -o codebase.txt
npx repomix --include "setup.py,__test__/,pytest_root_config.py,pytest.ini" -o tests.txt
npx repomix --include "docs/arch/,docs/guides/,docs/planning/,README.md" -o docs.txt
