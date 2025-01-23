npx repomix --include "auth/,configs/,domain/,infrastructure/,metadata/,orm/,repositories/,routers/,schemas/,services/,utils/,dependencies.py,main.py,setup.py" -o codebase.txt
npx repomix --include "conftest.py,setup.py,__tests__/,pytest_root_config.py,pytest.ini" -o tests.txt
npx repomix --include "docs/,README.md" -o docs.txt

# Pack document feature files
npx repomix --include "domain/document.py,orm/DocumentModel.py,repositories/DocumentRepository.py,services/DocumentService.py,routers/v1/DocumentRouter.py,schemas/pydantic/DocumentSchema.py,__tests__/unit/domain/test_document.py,__tests__/unit/repositories/test_document_repository.py,__tests__/unit/services/test_document_service.py,docs/guides/api-documentation.md,docs/planning/docs-entity.md,configs/OpenAPI.py,utils/validation/validation.py,utils/errors/domain_exceptions.py" -o document-feature.txt

# Pack storage feature files
npx repomix --include "domain/storage.py,infrastructure/storage/local.py,infrastructure/storage/s3_storage.py,infrastructure/storage/__init__.py,docs/guides/s3-storage.md,__tests__/unit/infrastructure/storage/test_local_storage.py,__tests__/unit/infrastructure/storage/test_s3_storage.py,utils/errors/storage_exceptions.py" -o storage-feature.txt
