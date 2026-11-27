# AWS infrastructure reference and legacy file register

Verified 2026-11-27; account 376129856177, us-east-1. Production servers are AWS-only. This source branch is not deployed. Canonical system map: MycosoftLabs/mycosoft-mas root `MYCOSOFT_AWS_INFRA_CURRENT.md`.

Source base: `cd52c61297bf1209824806913ccd015c1380826d`. Supplied Grok patches are rebased by exact hunk context/three-way merge; unavailable MycoBrain base ef93c57 was reconciled against current main using complete matching context. Historical code bodies remain present.

## Configuration

MINDEX: `http://mindex-internal.mycosoft.com:8000`; MAS: `http://mas-internal.mycosoft.com:8001`; MycoBrain: `http://mycobrain-internal.mycosoft.com:8003`. Mycorrhizae uses `http://internal-mycosoft-core-int-21300503.us-east-1.elb.amazonaws.com:8002`; n8n MAS/MYCA use the same internal ALB ports5678/5679. Website is `https://mycosoft.com`; Origin is `https://origin-aws.mycosoft.com:8443`. These private backends are server-side only. Never put service secrets into NEXT_PUBLIC variables. Database access uses Secrets Manager application credentials and the TLS-verified RDS Proxy; see the canonical map.

Unknown optional LAN/hypervisor/device integrations need explicit configuration and separate verification; a retained literal in those bodies is not a discovered AWS replacement. Tests, source datasets, migrations and signed records retain evidence. Retired CLI guards only stop the standalone old SSH/Proxmox utility; importable library bodies remain. AWS-aware utilities were preserved. Production AWS services were not restarted or redeployed.

## GitHub workflow inventory

No tracked GitHub Actions workflows found at this source base.

## Complete matching-file register

Rows are a reviewed inventory, not evidence that an optional connector is used in production. Each replacement either points to the verified AWS service, retires the local topology instruction, or preserves a non-current evidence/configuration record.

| File | Disposition | Replacement / retained-reference meaning |
|---|---|---|
| `.env.example` | AWS / AWS_ENDPOINTS_CORRECTED | redis://192.168.0.189:6379 -> rediss://master.mycosoft-prod-valkey.7kzq8i.use1.cache.amazonaws.com:6379 |
| `README.md` | AWS / LEGACY_DOCUMENT_CORRECTED | redis://192.168.0.189:6379 -> rediss://master.mycosoft-prod-valkey.7kzq8i.use1.cache.amazonaws.com:6379 |
| `api/main.py` | AWS / AWS_ENDPOINTS_CORRECTED | http://192.168.0.187:3000 -> removed from browser CORS defaults; http://192.168.0.188:8001 -> removed from browser CORS defaults; http://192.168.0.189:8000 -> removed from browser CORS defaults |
| `docker-compose.vm188.yml` | RET / HISTORICAL_OR_EXTERNAL_REFERENCE | Use the AWS service/Secrets Manager configuration matrix; no LAN/VM/NAS production target. Retained text is historical, fixture data or an optional external connector. |
| `docs/FUNGAL_COMPUTER_INTERFACE_FEB10_2026.md` | AWS / LEGACY_DOCUMENT_CORRECTED | http://192.168.0.188:8002 -> http://internal-mycosoft-core-int-21300503.us-east-1.elb.amazonaws.com:8002 |
| `docs/GLOBAL_FUNGI_SYMBIOSIS_THEORY_FEB10_2026.md` | RET / RETIRED_LOCAL_REFERENCE_OR_OPTIONAL_EXTERNAL_CONNECTOR | Retired local topology; use the verified AWS service map. No AWS counterpart is asserted for physical device fixtures, archival records, or optional hypervisor/network connectors. |
| `docs/HPL_LANGUAGE_GUIDE_FEB10_2026.md` | RET / LEGACY_DOCUMENT_CORRECTED | Use the AWS service/Secrets Manager configuration matrix; no LAN/VM/NAS production target. Retained text is historical, fixture data or an optional external connector. |
| `docs/MYCORRHIZAE_API_REFERENCE_FEB10_2026.md` | AWS / LEGACY_DOCUMENT_CORRECTED | http://192.168.0.188:8002 -> http://internal-mycosoft-core-int-21300503.us-east-1.elb.amazonaws.com:8002 |
| `docs/MYCORRHIZAE_INTEGRATION_GUIDE_FEB10_2026.md` | AWS / LEGACY_DOCUMENT_CORRECTED | http://192.168.0.188:8002 -> http://internal-mycosoft-core-int-21300503.us-east-1.elb.amazonaws.com:8002; redis://192.168.0.189:6379 -> rediss://master.mycosoft-prod-valkey.7kzq8i.use1.cache.amazonaws.com:6379 |
| `docs/MYCORRHIZAE_PROTOCOL_OVERVIEW_FEB10_2026.md` | AWS / LEGACY_DOCUMENT_CORRECTED | http://192.168.0.188:8002 -> http://internal-mycosoft-core-int-21300503.us-east-1.elb.amazonaws.com:8002; redis://192.168.0.189:6379 -> rediss://master.mycosoft-prod-valkey.7kzq8i.use1.cache.amazonaws.com:6379 |
| `mycorrhizae/integrations/mindex_client.py` | AWS / AWS_ENDPOINTS_CORRECTED | http://192.168.0.189:8000 -> http://mindex-internal.mycosoft.com:8000 |
| `scripts/bootstrap_api_keys_FEB09_2026.py` | RET / HISTORICAL_OR_EXTERNAL_REFERENCE | Use the AWS service/Secrets Manager configuration matrix; no LAN/VM/NAS production target. Retained text is historical, fixture data or an optional external connector. |
