import { MigrationInterface, QueryRunner, Table, TableIndex, TableForeignKey } from "typeorm";

export class Createblogtables20251208140640 implements MigrationInterface {
    name = 'Createblogtables20251208140640'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.createTable(
            new Table({
                name: "user",
                columns: [
                    {
                        name: "id",
                        type: "int",
                        isPrimary: true,
                        isGenerated: true,
                        generationStrategy: "increment",
                        isNullable: false,
                    },
                    {
                        name: "username",
                        type: "varchar",
                        length: "50",
                        isNullable: false,
                        isUnique: true,
                    },
                    {
                        name: "email",
                        type: "varchar",
                        length: "100",
                        isNullable: false,
                        isUnique: true,
                    },
                    {
                        name: "password_hash",
                        type: "varchar",
                        length: "255",
                        isNullable: false,
                    },
                    {
                        name: "first_name",
                        type: "varchar",
                        length: "100",
                    },
                    {
                        name: "last_name",
                        type: "varchar",
                        length: "100",
                    },
                    {
                        name: "is_active",
                        type: "boolean",
                        default: true,
                    },
                    {
                        name: "is_admin",
                        type: "boolean",
                        default: false,
                    },
                    {
                        name: "created_at",
                        type: "timestamp",
                        default: "CURRENT_TIMESTAMP",
                    },
                    {
                        name: "updated_at",
                        type: "timestamp",
                    },
                ],
            }),
            true
        );

        await queryRunner.createIndex(
            "user",
            new TableIndex({
                name: "IDX_USER_EMAIL",
                columnNames: ["email"]
            })
        );

        await queryRunner.createTable(
            new Table({
                name: "post",
                columns: [
                    {
                        name: "id",
                        type: "int",
                        isPrimary: true,
                        isGenerated: true,
                        generationStrategy: "increment",
                        isNullable: false,
                    },
                    {
                        name: "title",
                        type: "varchar",
                        length: "200",
                        isNullable: false,
                    },
                    {
                        name: "slug",
                        type: "varchar",
                        length: "200",
                        isNullable: false,
                        isUnique: true,
                    },
                    {
                        name: "content",
                        type: "text",
                    },
                    {
                        name: "excerpt",
                        type: "varchar",
                        length: "500",
                    },
                    {
                        name: "user_id",
                        type: "int",
                        isNullable: false,
                    },
                    {
                        name: "published",
                        type: "boolean",
                        default: false,
                    },
                    {
                        name: "view_count",
                        type: "int",
                        default: 0,
                    },
                    {
                        name: "created_at",
                        type: "timestamp",
                        default: "CURRENT_TIMESTAMP",
                    },
                    {
                        name: "updated_at",
                        type: "timestamp",
                    },
                ],
            }),
            true
        );

        await queryRunner.createIndex(
            "post",
            new TableIndex({
                name: "IDX_POST_TITLE",
                columnNames: ["title"]
            })
        );

        await queryRunner.createTable(
            new Table({
                name: "comment",
                columns: [
                    {
                        name: "id",
                        type: "int",
                        isPrimary: true,
                        isGenerated: true,
                        generationStrategy: "increment",
                        isNullable: false,
                    },
                    {
                        name: "post_id",
                        type: "int",
                        isNullable: false,
                    },
                    {
                        name: "user_id",
                        type: "int",
                        isNullable: false,
                    },
                    {
                        name: "content",
                        type: "text",
                        isNullable: false,
                    },
                    {
                        name: "approved",
                        type: "boolean",
                        default: false,
                    },
                    {
                        name: "created_at",
                        type: "timestamp",
                        default: "CURRENT_TIMESTAMP",
                    },
                ],
            }),
            true
        );

        await queryRunner.createTable(
            new Table({
                name: "tag",
                columns: [
                    {
                        name: "id",
                        type: "int",
                        isPrimary: true,
                        isGenerated: true,
                        generationStrategy: "increment",
                        isNullable: false,
                    },
                    {
                        name: "name",
                        type: "varchar",
                        length: "50",
                        isNullable: false,
                        isUnique: true,
                    },
                    {
                        name: "slug",
                        type: "varchar",
                        length: "50",
                        isNullable: false,
                        isUnique: true,
                    },
                    {
                        name: "created_at",
                        type: "timestamp",
                        default: "CURRENT_TIMESTAMP",
                    },
                ],
            }),
            true
        );

    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.dropTable("tag");
        await queryRunner.dropTable("comment");
        await queryRunner.dropIndex("post", "IDX_POST_TITLE");
        await queryRunner.dropTable("post");
        await queryRunner.dropIndex("user", "IDX_USER_EMAIL");
        await queryRunner.dropTable("user");
    }
}
