<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('marketing_agent_campaigns', function (Blueprint $table): void {
            $table->uuid('id')->primary();
            $table->string('title', 240);
            $table->text('source_url')->nullable();
            $table->string('language', 32)->default('Tamil');
            $table->string('status', 40)->default('pending_approval')->index();
            $table->jsonb('input_data');
            $table->jsonb('plan');
            $table->jsonb('trypost_response')->nullable();
            $table->text('error_message')->nullable();
            $table->timestampTz('approved_at')->nullable();
            $table->timestampsTz();
        });

        DB::statement('ALTER TABLE marketing_agent_campaigns ENABLE ROW LEVEL SECURITY');
        DB::statement(<<<'SQL'
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    REVOKE ALL ON TABLE marketing_agent_campaigns FROM anon;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    REVOKE ALL ON TABLE marketing_agent_campaigns FROM authenticated;
                END IF;
            END
            $$;
        SQL);
    }

    public function down(): void
    {
        Schema::dropIfExists('marketing_agent_campaigns');
    }
};
