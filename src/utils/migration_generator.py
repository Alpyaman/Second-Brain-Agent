"""
Database Migration Generator

Automatically generates database migration files for various ORMs:
- Alembic (SQLAlchemy)
- Django ORM
- Prisma
- TypeORM
- Sequelize

Usage:
    from src.utils.migration_generator import MigrationGenerator
    
    generator = MigrationGenerator()
    
    # Generate from schema
    migration = generator.generate_alembic_migration(schema, "add_users_table")
    
    # Generate from models
    migration = generator.generate_django_migration(models, "0001_initial")
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Column:
    """Represents a database column."""
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: Optional[str] = None
    foreign_key: Optional[Tuple[str, str]] = None  # (table, column)
    index: bool = False


@dataclass
class Table:
    """Represents a database table."""
    name: str
    columns: List[Column]
    indexes: List[str] = None
    unique_constraints: List[List[str]] = None
    
    def __post_init__(self):
        if self.indexes is None:
            self.indexes = []
        if self.unique_constraints is None:
            self.unique_constraints = []


class MigrationGenerator:
    """Generate database migrations for various ORMs."""
    
    def __init__(self):
        self.logger = logger
    
    def parse_schema_from_text(self, schema_text: str) -> List[Table]:
        """
        Parse schema from text description.
        
        Example:
            User table:
                id: integer, primary key
                username: string(50), unique
                email: string(100), unique
                created_at: datetime
        """
        tables = []
        current_table = None
        current_columns = []
        
        lines = schema_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Table definition
            if line.lower().endswith('table:') or line.lower().endswith('model:'):
                if current_table:
                    tables.append(Table(name=current_table, columns=current_columns))
                current_table = line.split()[0]
                current_columns = []
            
            # Column definition
            elif ':' in line and current_table:
                col = self._parse_column(line)
                if col:
                    current_columns.append(col)
        
        # Add last table
        if current_table:
            tables.append(Table(name=current_table, columns=current_columns))
        
        return tables
    
    def _parse_column(self, line: str) -> Optional[Column]:
        """Parse a single column definition."""
        try:
            parts = line.split(':', 1)
            if len(parts) != 2:
                return None
            
            name = parts[0].strip()
            spec = parts[1].strip().lower()
            
            # Parse type
            type_match = re.match(r'(\w+)(?:\((\d+)\))?', spec)
            if not type_match:
                return None
            
            col_type = type_match.group(1)
            col_length = type_match.group(2)
            
            if col_length:
                col_type = f"{col_type}({col_length})"
            
            # Parse constraints
            nullable = 'not null' not in spec and 'primary key' not in spec
            primary_key = 'primary key' in spec or 'pk' in spec
            unique = 'unique' in spec
            index = 'index' in spec
            
            # Parse default
            default = None
            default_match = re.search(r'default[:\s]+([^\s,]+)', spec)
            if default_match:
                default = default_match.group(1)
            
            # Parse foreign key
            foreign_key = None
            fk_match = re.search(r'foreign key[:\s]+(\w+)\.(\w+)', spec)
            if fk_match:
                foreign_key = (fk_match.group(1), fk_match.group(2))
            
            return Column(
                name=name,
                type=col_type,
                nullable=nullable,
                primary_key=primary_key,
                unique=unique,
                default=default,
                foreign_key=foreign_key,
                index=index
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse column: {line}. Error: {e}")
            return None
    
    def generate_alembic_migration(
        self, 
        tables: List[Table], 
        migration_name: str,
        message: Optional[str] = None
    ) -> str:
        """
        Generate Alembic (SQLAlchemy) migration.
        
        Args:
            tables: List of Table objects
            migration_name: Name of the migration
            message: Optional migration message
        
        Returns:
            Migration file content
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        revision = datetime.now().strftime("%Y%m%d%H%M%S")
        
        migration = f'''"""
{migration_name}

Revision ID: {revision}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '{revision}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration."""
'''
        
        # Generate table creation
        for table in tables:
            migration += f"    # Create {table.name} table\n"
            migration += "    op.create_table(\n"
            migration += f"        '{table.name.lower()}',\n"
            
            # Columns
            for col in table.columns:
                col_def = self._get_sqlalchemy_column(col)
                migration += f"        {col_def},\n"
            
            migration += "    )\n\n"
            
            # Indexes
            for col in table.columns:
                if col.index and not col.primary_key:
                    migration += "    op.create_index(\n"
                    migration += f"        'ix_{table.name.lower()}_{col.name}',\n"
                    migration += f"        '{table.name.lower()}',\n"
                    migration += f"        ['{col.name}']\n"
                    migration += "    )\n\n"
        
        migration += "\n\ndef downgrade():\n"
        migration += "    \"\"\"Revert migration.\"\"\"\n"
        
        # Generate table drops (reverse order)
        for table in reversed(tables):
            # Drop indexes first
            for col in table.columns:
                if col.index and not col.primary_key:
                    migration += f"    op.drop_index('ix_{table.name.lower()}_{col.name}')\n"
            
            migration += f"    op.drop_table('{table.name.lower()}')\n"
        
        return migration
    
    def _get_sqlalchemy_column(self, col: Column) -> str:
        """Generate SQLAlchemy column definition."""
        type_map = {
            'integer': 'sa.Integer',
            'int': 'sa.Integer',
            'bigint': 'sa.BigInteger',
            'string': 'sa.String',
            'text': 'sa.Text',
            'boolean': 'sa.Boolean',
            'bool': 'sa.Boolean',
            'datetime': 'sa.DateTime',
            'date': 'sa.Date',
            'time': 'sa.Time',
            'float': 'sa.Float',
            'decimal': 'sa.Numeric',
            'json': 'sa.JSON',
            'uuid': 'postgresql.UUID',
        }
        
        # Get base type
        base_type = col.type.split('(')[0].lower()
        sa_type = type_map.get(base_type, 'sa.String')
        
        # Add length for string types
        if 'string' in col.type.lower() and '(' in col.type:
            length = col.type.split('(')[1].split(')')[0]
            sa_type = f"sa.String({length})"
        
        parts = [f"sa.Column('{col.name}', {sa_type}"]
        
        if col.primary_key:
            parts.append("primary_key=True")
        
        if not col.nullable:
            parts.append("nullable=False")
        
        if col.unique:
            parts.append("unique=True")
        
        if col.default:
            if col.default.lower() in ['true', 'false']:
                parts.append(f"default={col.default.capitalize()}")
            elif col.default.isdigit():
                parts.append(f"default={col.default}")
            else:
                parts.append(f"default='{col.default}'")
        
        if col.foreign_key:
            fk_table, fk_column = col.foreign_key
            parts.append(f"sa.ForeignKey('{fk_table.lower()}.{fk_column}')")
        
        return ', '.join(parts) + ')'
    
    def generate_django_migration(
        self,
        tables: List[Table],
        migration_number: str = "0001"
    ) -> str:
        """
        Generate Django ORM migration.
        
        Args:
            tables: List of Table objects
            migration_number: Migration number (e.g., "0001", "0002")
        
        Returns:
            Migration file content
        """
        migration = f'''# Generated by Second Brain Agent on {datetime.now().strftime("%Y-%m-%d %H:%M")}

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
'''
        
        for table in tables:
            migration += "        migrations.CreateModel(\n"
            migration += f"            name='{table.name}',\n"
            migration += "            fields=[\n"
            
            for col in table.columns:
                col_def = self._get_django_field(col)
                migration += f"                {col_def},\n"
            
            migration += "            ],\n"
            
            # Add options
            migration += "            options={\n"
            migration += f"                'db_table': '{table.name.lower()}',\n"
            migration += "            },\n"
            migration += "        ),\n"
        
        # Add indexes
        for table in tables:
            index_cols = [col for col in table.columns if col.index and not col.primary_key]
            if index_cols:
                migration += "        migrations.AddIndex(\n"
                migration += f"            model_name='{table.name.lower()}',\n"
                migration += "            index=models.Index(fields=['"
                migration += "', '".join(col.name for col in index_cols)
                migration += f"'], name='idx_{table.name.lower()}_{'_'.join(col.name for col in index_cols[:2])}'),\n"
                migration += "        ),\n"
        
        migration += "    ]\n"
        
        return migration
    
    def _get_django_field(self, col: Column) -> str:
        """Generate Django model field definition."""
        type_map = {
            'integer': 'models.IntegerField',
            'int': 'models.IntegerField',
            'bigint': 'models.BigIntegerField',
            'string': 'models.CharField',
            'text': 'models.TextField',
            'boolean': 'models.BooleanField',
            'bool': 'models.BooleanField',
            'datetime': 'models.DateTimeField',
            'date': 'models.DateField',
            'time': 'models.TimeField',
            'float': 'models.FloatField',
            'decimal': 'models.DecimalField',
            'json': 'models.JSONField',
            'uuid': 'models.UUIDField',
        }
        
        base_type = col.type.split('(')[0].lower()
        django_type = type_map.get(base_type, 'models.CharField')
        
        parts = [f"('{col.name}', {django_type}("]
        field_args = []
        
        # Add max_length for CharField
        if 'char' in django_type.lower() and '(' in col.type:
            length = col.type.split('(')[1].split(')')[0]
            field_args.append(f"max_length={length}")
        
        if col.primary_key:
            field_args.append("primary_key=True")
        
        if col.unique:
            field_args.append("unique=True")
        
        if col.nullable:
            field_args.append("null=True")
            field_args.append("blank=True")
        
        if col.default:
            if col.default.lower() in ['true', 'false']:
                field_args.append(f"default={col.default.capitalize()}")
            elif col.default.isdigit():
                field_args.append(f"default={col.default}")
            else:
                field_args.append(f"default='{col.default}'")
        
        if col.foreign_key:
            fk_table, fk_column = col.foreign_key
            parts = [f"('{col.name}', models.ForeignKey("]
            field_args = [
                f"'{fk_table}'",
                "on_delete=models.CASCADE"
            ]
        
        return parts[0] + ', '.join(field_args) + ')))'
    
    def generate_prisma_migration(
        self,
        tables: List[Table],
        migration_name: str
    ) -> str:
        """
        Generate Prisma migration.
        
        Args:
            tables: List of Table objects
            migration_name: Name of the migration
        
        Returns:
            Prisma schema content
        """
        schema = f'''// Generated by Second Brain Agent
// Migration: {migration_name}
// Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

generator client {{
  provider = "prisma-client-js"
}}

datasource db {{
  provider = "postgresql"
  url      = env("DATABASE_URL")
}}

'''
        
        for table in tables:
            schema += f"model {table.name} {{\n"
            
            for col in table.columns:
                col_def = self._get_prisma_field(col)
                schema += f"  {col_def}\n"
            
            # Add indexes
            index_cols = [col for col in table.columns if col.index and not col.primary_key]
            if index_cols:
                schema += f"\n  @@index([{', '.join(col.name for col in index_cols)}])\n"
            
            schema += "}\n\n"
        
        return schema
    
    def _get_prisma_field(self, col: Column) -> str:
        """Generate Prisma field definition."""
        type_map = {
            'integer': 'Int',
            'int': 'Int',
            'bigint': 'BigInt',
            'string': 'String',
            'text': 'String',
            'boolean': 'Boolean',
            'bool': 'Boolean',
            'datetime': 'DateTime',
            'date': 'DateTime',
            'float': 'Float',
            'decimal': 'Decimal',
            'json': 'Json',
            'uuid': 'String',
        }
        
        base_type = col.type.split('(')[0].lower()
        prisma_type = type_map.get(base_type, 'String')
        
        optional = '?' if col.nullable else ''
        
        parts = [f"{col.name} {prisma_type}{optional}"]
        
        attributes = []
        
        if col.primary_key:
            attributes.append("@id @default(autoincrement())")
        
        if col.unique:
            attributes.append("@unique")
        
        if col.default and not col.primary_key:
            if col.default.lower() in ['true', 'false']:
                attributes.append(f"@default({col.default.lower()})")
            elif col.default.lower() == 'now':
                attributes.append("@default(now())")
            elif col.default.isdigit():
                attributes.append(f"@default({col.default})")
            else:
                attributes.append(f'@default("{col.default}")')
        
        if col.foreign_key:
            fk_table, fk_column = col.foreign_key
            parts = [f"{col.name}   {fk_table}"]
            attributes.append(f"@relation(fields: [{col.name}Id], references: [{fk_column}])")
        
        if attributes:
            parts.append(' '.join(attributes))
        
        return ' '.join(parts)
    
    def generate_typeorm_migration(
        self,
        tables: List[Table],
        migration_name: str
    ) -> str:
        """
        Generate TypeORM migration.
        
        Args:
            tables: List of Table objects
            migration_name: Name of the migration
        
        Returns:
            TypeORM migration file content
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        class_name = ''.join(word.capitalize() for word in migration_name.split('_'))
        
        migration = f'''import {{ MigrationInterface, QueryRunner, Table, TableIndex, TableForeignKey }} from "typeorm";

export class {class_name}{timestamp} implements MigrationInterface {{
    name = '{class_name}{timestamp}'

    public async up(queryRunner: QueryRunner): Promise<void> {{
'''
        
        for table in tables:
            migration += "        await queryRunner.createTable(\n"
            migration += "            new Table({\n"
            migration += f'                name: "{table.name.lower()}",\n'
            migration += "                columns: [\n"
            
            for col in table.columns:
                col_def = self._get_typeorm_column(col)
                migration += f'                    {col_def},\n'
            
            migration += '                ],\n'
            migration += '            }),\n'
            migration += '            true\n'
            migration += '        );\n\n'
            
            # Add indexes
            for col in table.columns:
                if col.index and not col.primary_key:
                    migration += "        await queryRunner.createIndex(\n"
                    migration += f'            "{table.name.lower()}",\n'
                    migration += "            new TableIndex({\n"
                    migration += f'                name: "IDX_{table.name.upper()}_{col.name.upper()}",\n'
                    migration += f'                columnNames: ["{col.name}"]\n'
                    migration += "            })\n"
                    migration += "        );\n\n"
        
        migration += '    }\n\n'
        migration += '    public async down(queryRunner: QueryRunner): Promise<void> {\n'
        
        for table in reversed(tables):
            # Drop indexes first
            for col in table.columns:
                if col.index and not col.primary_key:
                    migration += f'        await queryRunner.dropIndex("{table.name.lower()}", "IDX_{table.name.upper()}_{col.name.upper()}");\n'
            
            migration += f'        await queryRunner.dropTable("{table.name.lower()}");\n'
        
        migration += '    }\n'
        migration += '}\n'
        
        return migration
    
    def _get_typeorm_column(self, col: Column) -> str:
        """Generate TypeORM column definition."""
        type_map = {
            'integer': 'int',
            'int': 'int',
            'bigint': 'bigint',
            'string': 'varchar',
            'text': 'text',
            'boolean': 'boolean',
            'bool': 'boolean',
            'datetime': 'timestamp',
            'date': 'date',
            'time': 'time',
            'float': 'float',
            'decimal': 'decimal',
            'json': 'json',
            'uuid': 'uuid',
        }
        
        base_type = col.type.split('(')[0].lower()
        typeorm_type = type_map.get(base_type, 'varchar')
        
        parts = ['{']
        parts.append(f'\n                        name: "{col.name}",')
        parts.append(f'\n                        type: "{typeorm_type}",')
        
        if 'varchar' in typeorm_type and '(' in col.type:
            length = col.type.split('(')[1].split(')')[0]
            parts.append(f'\n                        length: "{length}",')
        
        if col.primary_key:
            parts.append('\n                        isPrimary: true,')
            parts.append('\n                        isGenerated: true,')
            parts.append('\n                        generationStrategy: "increment",')
        
        if not col.nullable:
            parts.append('\n                        isNullable: false,')
        
        if col.unique:
            parts.append('\n                        isUnique: true,')
        
        if col.default:
            if col.default.lower() in ['true', 'false']:
                parts.append(f'\n                        default: {col.default.lower()},')
            elif col.default.lower() == 'now':
                parts.append('\n                        default: "CURRENT_TIMESTAMP",')
            elif col.default.isdigit():
                parts.append(f'\n                        default: {col.default},')
            else:
                parts.append(f'\n                        default: "{col.default}",')
        
        parts.append('\n                    }')
        
        return ''.join(parts)
    
    def save_migration(
        self,
        content: str,
        output_dir: Path,
        migration_type: str,
        migration_name: str
    ) -> Path:
        """
        Save migration file to disk.
        
        Args:
            content: Migration content
            output_dir: Output directory
            migration_type: Type of migration (alembic, django, prisma, typeorm)
            migration_name: Name of the migration
        
        Returns:
            Path to saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if migration_type == 'alembic':
            filename = f"{timestamp}_{migration_name}.py"
        elif migration_type == 'django':
            filename = f"0001_{migration_name}.py"
        elif migration_type == 'prisma':
            filename = "schema.prisma"
        elif migration_type == 'typeorm':
            filename = f"{timestamp}-{migration_name}.ts"
        else:
            filename = f"{migration_name}.sql"
        
        file_path = output_dir / filename
        file_path.write_text(content, encoding='utf-8')
        
        self.logger.info(f"Migration saved to: {file_path}")
        return file_path


def main():
    """Example usage."""
    generator = MigrationGenerator()
    
    # Example schema
    schema_text = """
    User table:
        id: integer, primary key
        username: string(50), unique, not null
        email: string(100), unique, not null
        password_hash: string(255), not null
        created_at: datetime, default: now
        updated_at: datetime
    
    Post table:
        id: integer, primary key
        title: string(200), not null
        content: text
        user_id: integer, foreign key: User.id, not null
        published: boolean, default: false
        created_at: datetime, default: now
    """
    
    tables = generator.parse_schema_from_text(schema_text)
    
    print("=== Alembic Migration ===")
    alembic = generator.generate_alembic_migration(tables, "add_user_and_post_tables")
    print(alembic)
    
    print("\n=== Django Migration ===")
    django = generator.generate_django_migration(tables)
    print(django)
    
    print("\n=== Prisma Migration ===")
    prisma = generator.generate_prisma_migration(tables, "add_user_and_post")
    print(prisma)


if __name__ == "__main__":
    main()
