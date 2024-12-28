npx repomix --include "configs/,domain/,infrastructure/,metadata/,orm/,repositories/,routers/,schemas/,services/,utils/,dependencies.py,main.py,setup.py" -o codebase.txt
npx repomix --include "conftest.py,setup.py,__tests__/,pytest_root_config.py,pytest.ini" -o tests.txt
npx repomix --include "docs/,README.md" -o docs.txt
