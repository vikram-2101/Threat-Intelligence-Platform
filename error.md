tip-worker | [2026-04-18 11:16:32,766: ERROR/ForkPoolWorker-4] Task app.workers.tasks.fetch*external_feeds[3955e1a3-f4c1-4a5f-b25f-6defbc578b6d] raised unexpected: ProgrammingError('(psycopg2.errors.UndefinedColumn) column sources.last_pull_at does not exist\nLINE 1: ...schedule, sources.is_active AS sources_is_active, sources.la...\n  
 ^\n')
tip-worker | Traceback (most recent call last):
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1967, in \_exec_single_context
tip-worker | self.dialect.do_execute(
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute  
tip-worker | cursor.execute(statement, parameters)
tip-worker | psycopg2.errors.UndefinedColumn: column sources.last_pull_at does not exist  
tip-worker | LINE 1: ...schedule, sources.is_active AS sources_is_active, sources.la...  
tip-worker | ^  
tip-worker |
tip-worker |  
tip-worker | The above exception was the direct cause of the following exception:  
tip-worker |
tip-worker | Traceback (most recent call last):  
tip-worker | File "/usr/local/lib/python3.12/site-packages/celery/app/trace.py", line 585, in trace_task  
tip-worker | R = retval = fun(*args, \*\*kwargs)
tip-worker | ^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/celery/app/trace.py", line 858, in **protected_call**  
tip-worker | return self.run(*args, \*\*kwargs)
tip-worker | ^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/app/app/workers/tasks.py", line 26, in fetch_external_feeds  
tip-worker | ).all()
tip-worker | ^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/query.py", line 2711, in all  
tip-worker | return self.\_iter().all() # type: ignore  
tip-worker | ^^^^^^^^^^^^
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/query.py", line 2864, in \_iter  
tip-worker | result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(  
tip-worker | ^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2351, in execute  
tip-worker | return self.\_execute_internal(
tip-worker | ^^^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2249, in \_execute_internal
tip-worker | result: Result[Any] = compile_state_cls.orm_execute_statement(  
tip-worker | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
tip-worker | result = conn.execute(
tip-worker | ^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1419, in execute  
tip-worker | return meth(
tip-worker | ^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 527, in \_execute_on_connection
tip-worker | return connection.\_execute_clauseelement(  
tip-worker | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1641, in \_execute_clauseelement
tip-worker | ret = self.\_execute_context(
tip-worker | ^^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1846, in \_execute_context
tip-worker | return self.\_exec_single_context(
tip-worker | ^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1986, in \_exec_single_context
tip-worker | self.\_handle_dbapi_exception(
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2363, in \_handle_dbapi_exception
tip-worker | raise sqlalchemy_exception.with_traceback(exc_info[2]) from e  
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1967, in \_exec_single_context
tip-worker | self.dialect.do_execute(
tip-worker | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute  
tip-worker | cursor.execute(statement, parameters)
tip-worker | sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column sources.last_pull_at does not exist
tip-worker | LINE 1: ...schedule, sources.is_active AS sources_is_active, sources.la...  
tip-worker | ^  
tip-worker |
tip-worker | [SQL: SELECT sources.id AS sources_id, sources.name AS sources_name, sources.category AS sources_category, sources.trust_tier AS sources_trust_tier, sources.default_weight AS sources_default_weight, sources.intent_description AS sources_intent_description, sources.pull_url AS sources_pull_url, sources.pull_schedule AS sources_pull_schedule, sources.is_active AS sources_is_active, sources.last_pull_at AS sources_last_pull_at, sources.last_pull_status AS sources_last_pull_status, sources.created_at AS sources_created_at
tip-worker | FROM sources
tip-worker | WHERE sources.is_active = true AND sources.pull_url IS NOT NULL]  
tip-worker | (Background on this error at: https://sqlalche.me/e/20/f405)  
tip-postgres | 2026-04-18 11:17:16.079 UTC [41] ERROR: null value in column "entity_type" of relation "audit_logs" violates not-null constraint
tip-postgres | 2026-04-18 11:17:16.079 UTC [41] DETAIL: Failing row contains (e804d3aa-0050-41b6-9424-7cc2d5aae655, null, POST /api/v1/indicators/, null, null, {"client_ip": "172.20.0.1", "user_agent": "Mozilla/5.0 (Windows ..., null, t, 2026-04-18 11:17:16.078193+00).
tip-postgres | 2026-04-18 11:17:16.079 UTC [41] STATEMENT: INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, details, ip_address, is_active) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::UUID, $6::JSONB, $7, $8::BOOLEAN) RETURNING audit_logs.timestamp
tip-api | INFO: 172.20.0.1:48368 - "POST /api/v1/indicators/ HTTP/1.1" 401 Unauthorized  
tip-postgres | 2026-04-18 11:17:32.106 UTC [41] ERROR: null value in column "entity_type" of relation "audit_logs" violates not-null constraint
tip-postgres | 2026-04-18 11:17:32.106 UTC [41] DETAIL: Failing row contains (6796dc0f-e771-45cd-b064-c3dc3378ae84, null, POST /api/v1/auth/login, null, null, {"client_ip": "172.20.0.1", "user_agent": "Mozilla/5.0 (Windows ..., null, t, 2026-04-18 11:17:32.106333+00).
tip-postgres | 2026-04-18 11:17:32.106 UTC [41] STATEMENT: INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, details, ip_address, is_active) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::UUID, $6::JSONB, $7, $8::BOOLEAN) RETURNING audit_logs.timestamp
tip-api | INFO: 172.20.0.1:34492 - "POST /api/v1/auth/login HTTP/1.1" 200 OK  
tip-postgres | 2026-04-18 11:19:11.130 UTC [46] ERROR: null value in column "entity_type" of relation "audit_logs" violates not-null constraint
tip-postgres | 2026-04-18 11:19:11.130 UTC [46] DETAIL: Failing row contains (c97cef90-3d3a-494c-92bd-eb9441e37bf0, null, POST /api/v1/auth/login, null, null, {"client_ip": "172.20.0.1", "user_agent": "Mozilla/5.0 (Windows ..., null, t, 2026-04-18 11:19:11.130276+00).
tip-postgres | 2026-04-18 11:19:11.130 UTC [46] STATEMENT: INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, details, ip_address, is_active) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::UUID, $6::JSONB, $7, $8::BOOLEAN) RETURNING audit_logs.timestamp
tip-api | INFO: 172.20.0.1:60970 - "POST /api/v1/auth/login HTTP/1.1" 200 OK  
tip-postgres | 2026-04-18 11:19:55.192 UTC [46] ERROR: column "last_pull_at" of relation "sources" does not exist at character 126
tip-postgres | 2026-04-18 11:19:55.192 UTC [46] STATEMENT: INSERT INTO sources (id, name, category, trust_tier, default_weight, intent_description, pull_url, pull_schedule, is_active, last_pull_at, last_pull_status) VALUES ($1::UUID, $2::VARCHAR, $3::source_category, $4::trust_tier, $5::NUMERIC(3, 2), $6::VARCHAR, $7::VARCHAR, $8::VARCHAR, $9::BOOLEAN, $10::TIMESTAMP WITH TIME ZONE, $11::VARCHAR) RETURNING sources.created_at
tip-api | INFO: 172.20.0.1:57354 - "POST /api/v1/sources/ HTTP/1.1" 500 Internal Server Error  
tip-api | ERROR: Exception in ASGI application
tip-api | Traceback (most recent call last):
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in \_prepare_and_execute
tip-api | prepared_stmt, attributes = await adapt_connection.\_prepare(  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in \_prepare
tip-api | prepared_stmt = await self.\_connection.prepare(  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare  
tip-api | return await self.\_prepare(
tip-api | ^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in \_prepare  
tip-api | stmt = await self.\_get_statement(
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in \_get_statement  
tip-api | statement = await self.\_protocol.prepare(  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "asyncpg/protocol/protocol.pyx", line 165, in prepare
tip-api | asyncpg.exceptions.UndefinedColumnError: column "last_pull_at" of relation "sources" does not exist  
tip-api |
tip-api | The above exception was the direct cause of the following exception:  
tip-api |
tip-api | Traceback (most recent call last):  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1967, in \_exec_single_context
tip-api | self.dialect.do_execute(
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute  
tip-api | cursor.execute(statement, parameters)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
tip-api | self.\_adapt_connection.await*(
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/\_concurrency_py3k.py", line 132, in await_only
tip-api | return current.parent.switch(awaitable) # type: ignore[no-any-return,attr-defined] # noqa: E501  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/\_concurrency_py3k.py", line 196, in greenlet_spawn
tip-api | value = await result
tip-api | ^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in \_prepare_and_execute
tip-api | self.\_handle_exception(error)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in \_handle_exception
tip-api | self.\_adapt_connection.\_handle_exception(error)  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in \_handle_exception
tip-api | raise translated_error from error
tip-api | sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.ProgrammingError: <class 'asyncpg.exceptions.UndefinedColumnError'>: column "last_pull_at" of relation "sources" does not exist
tip-api |
tip-api | The above exception was the direct cause of the following exception:  
tip-api |
tip-api | Traceback (most recent call last):  
tip-api | File "/usr/local/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 420, in run_asgi
tip-api | result = await app( # type: ignore[func-returns-value]  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in **call**
tip-api | return await self.app(scope, receive, send)  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/fastapi/applications.py", line 1159, in **call**  
tip-api | await super().**call**(scope, receive, send)  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/applications.py", line 90, in **call**  
tip-api | await self.middleware_stack(scope, receive, send)  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in **call**  
tip-api | raise exc
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in **call**  
tip-api | await self.app(scope, receive, \_send)
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/base.py", line 191, in **call**  
tip-api | with recv_stream, send_stream, collapse_excgroups():  
tip-api | ^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/contextlib.py", line 158, in **exit**  
tip-api | self.gen.throw(value)
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/\_utils.py", line 87, in collapse_excgroups  
tip-api | raise exc
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in **call**  
tip-api | response = await self.dispatch_func(request, call_next)  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/app/app/api/middleware.py", line 15, in dispatch  
tip-api | response = await call_next(request)
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next  
tip-api | raise app_exc from app_exc.**cause** or app_exc.**context**  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro  
tip-api | await self.app(scope, receive_or_disconnect, send_no_error)  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in **call**
tip-api | await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/\_exception_handler.py", line 53, in wrapped_app
tip-api | raise exc
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/\_exception_handler.py", line 42, in wrapped_app
tip-api | await app(scope, receive, sender)
tip-api | File "/usr/local/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in **call**
tip-api | await self.app(scope, receive, send)
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/routing.py", line 660, in **call**  
tip-api | await self.middleware_stack(scope, receive, send)  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/routing.py", line 680, in app  
tip-api | await route.handle(scope, receive, send)
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle  
tip-api | await self.app(scope, receive, send)
tip-api | File "/usr/local/lib/python3.12/site-packages/fastapi/routing.py", line 134, in app  
tip-api | await wrap_app_handling_exceptions(app, request)(scope, receive, send)  
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/\_exception_handler.py", line 53, in wrapped_app
tip-api | raise exc
tip-api | File "/usr/local/lib/python3.12/site-packages/starlette/\_exception_handler.py", line 42, in wrapped_app
tip-api | await app(scope, receive, sender)
tip-api | File "/usr/local/lib/python3.12/site-packages/fastapi/routing.py", line 120, in app  
tip-api | response = await f(request)
tip-api | ^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/fastapi/routing.py", line 674, in app  
tip-api | raw_response = await run_endpoint_function(  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/fastapi/routing.py", line 328, in run_endpoint_function
tip-api | return await dependant.call(**values)
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/app/app/api/v1/endpoints/sources.py", line 27, in create_source  
tip-api | return await SourceService.create_source(db, source_in)  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/app/app/services/source_service.py", line 13, in create_source  
tip-api | await db.commit()
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 1000, in commit
tip-api | await greenlet_spawn(self.sync_session.commit)  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/\_concurrency_py3k.py", line 203, in greenlet_spawn
tip-api | result = context.switch(value)
tip-api | ^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2030, in commit  
tip-api | trans.commit(\_to_root=True)
tip-api | File "<string>", line 2, in commit  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/state_changes.py", line 137, in \_go  
tip-api | ret_value = fn(self, \*arg, **kw)
tip-api | ^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 1311, in commit  
tip-api | self.\_prepare_impl()
tip-api | File "<string>", line 2, in \_prepare_impl
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/state_changes.py", line 137, in \_go  
tip-api | ret_value = fn(self, \*arg, \*\*kw)
tip-api | ^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 1286, in \_prepare_impl
tip-api | self.session.flush()
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4331, in flush  
tip-api | self.\_flush(objects)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4466, in \_flush  
tip-api | with util.safe_reraise():
tip-api | ^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 121, in **exit**  
tip-api | raise exc_value.with_traceback(exc_tb)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4427, in \_flush  
tip-api | flush_context.execute()
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/unitofwork.py", line 466, in execute  
tip-api | rec.execute(self)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/unitofwork.py", line 642, in execute  
tip-api | util.preloaded.orm_persistence.save_obj(
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/persistence.py", line 93, in save_obj  
tip-api | \_emit_insert_statements(
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/persistence.py", line 1233, in \_emit_insert_statements
tip-api | result = connection.execute(
tip-api | ^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1419, in execute  
tip-api | return meth(
tip-api | ^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 527, in \_execute_on_connection
tip-api | return connection.\_execute_clauseelement(  
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1641, in \_execute_clauseelement
tip-api | ret = self.\_execute_context(
tip-api | ^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1846, in \_execute_context
tip-api | return self.\_exec_single_context(
tip-api | ^^^^^^^^^^^^^^^^^^^^^^^^^^  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1986, in \_exec_single_context
tip-api | self.\_handle_dbapi_exception(
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2363, in \_handle_dbapi_exception
tip-api | raise sqlalchemy_exception.with_traceback(exc_info[2]) from e  
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1967, in \_exec_single_context
tip-api | self.dialect.do_execute(
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute  
tip-api | cursor.execute(statement, parameters)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncnlet_spawn
tip-api | value = await result
tip-api | ^^^^^^^^^^^^
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in \_prepare_and_execute
tip-api | self.\_handle_exception(error)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in \_handle_exception
tip-api | self.\_adapt_connection.\_handle_exception(error)
tip-api | File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in \_handle_exception
tip-api | raise translated_error from error
tip-api | sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedColumnError'>: column "last_pull_at" of relation "sources" does not exist
tip-api | [SQL: INSERT INTO sources (id, name, category, trust_tier, default_weight, intent_description, pull_url, pull_schedule, is_active, last_pull_at, last_pull_status) VALUES ($1::UUID, $2::VARCHAR, $3::source_category, $4::trust_tier, $5::NUMERIC(3, 2), $6::VARCHAR, $7::VARCHAR, $8::VARCHAR, $9::BOOLEAN, $10::TIMESTAMP WITH TIME ZONE, $11::VARCHAR) RETURNING sources.created_at]  
tip-api | [parameters: (UUID('8bd2bded-e75a-4b53-92a5-b4c5af700154'), 'test-source', 'community', 'HIGH', 1.0, None, None, None, True, None, None)]
tip-api | (Background on this error at: https://sqlalche.me/e/20/f405)
