from pathlib import Path

path = Path("add_backend/app/services/ai_model_service.py")
text = path.read_text(encoding="utf-8")

start_marker = "async def generate_travel_response(request: ChatRequest) -> ChatResponse:"
end_marker = "\ndef safe_json_loads_from_model(raw_text: str):"

start = text.index(start_marker)
end = text.index(end_marker, start)

new_function = r'''async def generate_travel_response(request: ChatRequest) -> ChatResponse:
    logger.info("[GTR START] generate_travel_response entered")

    selected_model = request.model_variant or getattr(request, "selected_model", None) or "base"
    adapter_loaded = selected_model == "fine_tuned"

    backend_intent = detect_user_intent(request.message)
    logger.info("[BACKEND INTENT] %s", backend_intent)

    from add_backend.app.services.api_context_service import api_context_service

    enriched_api_context = await api_context_service.build_api_context_from_message(
        request.message,
        request.api_context
    )

    logger.info("[ENRICHED API CONTEXT] %s", json.dumps(enriched_api_context, indent=2, default=str))
    logger.info("[USED APIS] %s", enriched_api_context.get("used_apis", []))

    # Direct responses: do not load model
    if backend_intent == "weather_query":
        logger.info("[WEATHER DIRECT RESPONSE] Bypassing model")
        return await _build_direct_weather_response(request, enriched_api_context)

    if backend_intent == "flight_search":
        logger.info("[FLIGHT DIRECT RESPONSE] Bypassing model")
        return await _build_direct_flight_response(request, enriched_api_context)

    if backend_intent == "hotel_search":
        logger.info("[HOTEL DIRECT RESPONSE] Bypassing model")
        return await _build_direct_hotel_response(request, enriched_api_context)

    if MOCK_MODEL:
        logger.info("[MOCK MODEL RESPONSE]")
        return _build_intent_aware_mock_response(request, enriched_api_context)

    config = AdapterConfig.from_env()

    travel_info = enriched_api_context.get("travel_info", {}) or {}
    duration_days = travel_info.get("duration_days", 3)

    try:
        duration_days_int = int(duration_days)
    except Exception:
        duration_days_int = 3

    generation_tokens = request.max_new_tokens or safe_max_new_tokens(
        request.max_new_tokens,
        request.message
    )

    # Duration-aware token budget for itinerary
    if backend_intent == "itinerary_generation":
        if duration_days_int >= 10:
            generation_tokens = max(generation_tokens, 4500)
        elif duration_days_int >= 7:
            generation_tokens = max(generation_tokens, 3500)
        elif duration_days_int >= 4:
            generation_tokens = max(generation_tokens, 2500)
        else:
            generation_tokens = max(generation_tokens, 1500)

    logger.info("[FINAL GENERATION TOKENS] %s", generation_tokens)

    config = replace(config, model_max_new_tokens=generation_tokens)

    tokenizer, model = _get_model(selected_model, config)
    prompt = _build_prompt(request.message, enriched_api_context, backend_intent)

    raw_text = ""
    retry_raw_text = None
    retry_used = False
    parse_success = False
    fallback_used = False
    normalized = None
    parse_error = None

    try:
        logger.info("[MODEL GENERATION START] backend_intent=%s", backend_intent)
        raw_text = generate_text(tokenizer, model, prompt, config) or ""

        logger.info("[MODEL OUTPUT LENGTH] %s", len(raw_text))
        logger.info("[MODEL RAW OUTPUT] %r", raw_text)

        parsed = safe_json_loads_from_model(raw_text)
        dashboard_payload = parsed.get("dashboard_payload", parsed)

        # Itinerary quality validation
        if backend_intent == "itinerary_generation":
            if not itinerary_has_required_days(dashboard_payload, duration_days_int):
                raise ValueError("itinerary_missing_required_days")

            if itinerary_has_too_many_repeats(dashboard_payload, max_repeat=1):
                raise ValueError("itinerary_has_too_many_repeats")

            if not itinerary_has_required_diversity(dashboard_payload, duration_days_int):
                raise ValueError("itinerary_lacks_required_diversity")

        normalized_dashboard = normalize_model_dashboard_payload(
            dashboard_payload,
            backend_intent,
            enriched_api_context
        )

        normalized = {
            "assistant_message": parsed.get(
                "assistant_message",
                f"Here is a {duration_days_int}-day budget trip plan."
            ),
            "dashboard_payload": normalized_dashboard
        }

        normalized = enforce_api_context_truth(
            normalized,
            enriched_api_context,
            request.message
        )

        parse_success = True
        fallback_used = False
        retry_used = False

        if backend_intent == "itinerary_generation":
            normalized["dashboard_payload"]["itinerary_source"] = "model_generated"

    except Exception as first_exc:
        parse_error = first_exc
        logger.error("[MODEL FIRST ATTEMPT FAILED] %s", str(first_exc))
        logger.error("[MODEL FIRST RAW OUTPUT] %r", raw_text)

        if backend_intent == "itinerary_generation":
            retry_used = True

            retry_origin = travel_info.get("origin", "Origin")
            retry_destination = travel_info.get("destination", "Destination")

            retry_prompt = (
                "Return ONLY valid JSON. No markdown. No explanation outside JSON.\n"
                f"Create exactly {duration_days_int} days.\n"
                "Each day must contain exactly 3 items: Morning, Afternoon, Evening.\n"
                "Do not repeat the same activity more than once.\n"
                "Use varied attractions, neighborhoods, museums, parks, food areas, and cultural experiences.\n"
                "Do not include weather, flights, hotels, or local_events. Backend will inject those.\n"
                "Every itinerary item must have: day, time, activity, budget_eur.\n"
                "{\n"
                f'  "assistant_message": "Here is a {duration_days_int}-day budget trip plan from {retry_origin} to {retry_destination}.",\n'
                '  "dashboard_payload": {\n'
                '    "intent": "itinerary_generation",\n'
                '    "trip_summary": {\n'
                f'      "origin": "{retry_origin}",\n'
                f'      "destination": "{retry_destination}",\n'
                f'      "duration_days": {duration_days_int},\n'
                '      "budget": 500,\n'
                '      "currency": "EUR",\n'
                '      "source": "model_generated"\n'
                "    },\n"
                '    "food_recommendations": [\n'
                '      {"name": "Local budget food place", "price_range": "€5-10", "type": "local food"}\n'
                "    ],\n"
                '    "itinerary": [\n'
                '      {"day": 1, "time": "Morning", "activity": "Example unique activity", "budget_eur": 0}\n'
                "    ]\n"
                "  }\n"
                "}\n"
                f"USER REQUEST: {request.message}\n"
            )

            try:
                logger.info("[MODEL RETRY START]")
                retry_raw_text = generate_text(tokenizer, model, retry_prompt, config) or ""

                logger.info("[MODEL RETRY OUTPUT LENGTH] %s", len(retry_raw_text))
                logger.info("[MODEL RETRY RAW OUTPUT] %r", retry_raw_text)

                retry_parsed = safe_json_loads_from_model(retry_raw_text)
                retry_dashboard_payload = retry_parsed.get("dashboard_payload", retry_parsed)

                if not itinerary_has_required_days(retry_dashboard_payload, duration_days_int):
                    raise ValueError("retry_itinerary_missing_required_days")

                if itinerary_has_too_many_repeats(retry_dashboard_payload, max_repeat=1):
                    raise ValueError("retry_itinerary_has_too_many_repeats")

                if not itinerary_has_required_diversity(retry_dashboard_payload, duration_days_int):
                    raise ValueError("retry_itinerary_lacks_required_diversity")

                retry_normalized_dashboard = normalize_model_dashboard_payload(
                    retry_dashboard_payload,
                    backend_intent,
                    enriched_api_context
                )

                normalized = {
                    "assistant_message": retry_parsed.get(
                        "assistant_message",
                        f"Here is a {duration_days_int}-day budget trip plan from {retry_origin} to {retry_destination}."
                    ),
                    "dashboard_payload": retry_normalized_dashboard
                }

                normalized = enforce_api_context_truth(
                    normalized,
                    enriched_api_context,
                    request.message
                )

                parse_success = True
                fallback_used = False
                retry_used = True

                normalized["dashboard_payload"]["itinerary_source"] = "model_generated_retry"

            except Exception as retry_exc:
                parse_error = retry_exc
                logger.error("[MODEL RETRY FAILED] %s", str(retry_exc))
                logger.error("[MODEL RETRY RAW OUTPUT] %r", retry_raw_text)

                normalized = await build_static_fallback_from_context(
                    request=request,
                    backend_intent=backend_intent,
                    api_context=enriched_api_context
                )

                parse_success = False
                fallback_used = True
                retry_used = True

                normalized["dashboard_payload"]["intent"] = "itinerary_generation"
                normalized["dashboard_payload"]["itinerary"] = []
                normalized["dashboard_payload"]["food_recommendations"] = []
                normalized["dashboard_payload"]["itinerary_source"] = "model_failed"
                normalized["assistant_message"] = (
                    "The model could not generate a complete valid itinerary. "
                    "Please try again with fewer days or increase max_new_tokens."
                )

        else:
            normalized = await build_static_fallback_from_context(
                request=request,
                backend_intent=backend_intent,
                api_context=enriched_api_context
            )

            parse_success = False
            fallback_used = True
            retry_used = False

    # Final safety guard
    if normalized is None or not isinstance(normalized, dict) or "dashboard_payload" not in normalized:
        logger.error("[NORMALIZED GUARD] normalized missing, building default payload")

        normalized = {
            "assistant_message": "The model could not generate a valid response.",
            "dashboard_payload": build_default_dashboard_payload(backend_intent)
        }

        parse_success = False
        fallback_used = True

    dashboard_payload = normalized["dashboard_payload"]

    # For itinerary_generation:
    # keep model itinerary, inject API sections, calculate budget
    if backend_intent == "itinerary_generation":
        trip_summary = dashboard_payload.get("trip_summary") or {}

        origin = trip_summary.get("origin") or travel_info.get("origin")
        destination = trip_summary.get("destination") or travel_info.get("destination")

        dashboard_payload = await ensure_flights_for_route(
            dashboard_payload,
            enriched_api_context,
            origin,
            destination
        )

        dashboard_payload = merge_live_api_context_into_dashboard(
            dashboard_payload,
            enriched_api_context,
            backend_intent
        )

        dashboard_payload = await ensure_flights_for_route(
            dashboard_payload,
            enriched_api_context,
            origin,
            destination
        )

        dashboard_payload["budget_breakdown"] = calculate_budget_breakdown(dashboard_payload)
        dashboard_payload = update_dashboard_actions_for_available_sections(dashboard_payload)

        if "itinerary_source" not in dashboard_payload:
            dashboard_payload["itinerary_source"] = "model_generated" if parse_success else "model_failed"

        normalized["dashboard_payload"] = dashboard_payload

    response_kwargs = {}

    if request.include_raw_model_output:
        if parse_success and retry_used and retry_raw_text is not None:
            response_kwargs["raw_model_output"] = retry_raw_text
        elif parse_success:
            response_kwargs["raw_model_output"] = raw_text
        else:
            response_kwargs["raw_model_output"] = json.dumps(
                {
                    "first_raw_output": raw_text,
                    "retry_raw_output": retry_raw_text,
                    "error": str(parse_error)
                },
                default=str
            )

    logger.info(
        "[GTR RETURN] parse_success=%s fallback_used=%s retry_used=%s",
        parse_success,
        fallback_used,
        retry_used
    )

    return ChatResponse(
        session_id=request.session_id,
        selected_model=selected_model,
        adapter_loaded=adapter_loaded,
        parse_success=parse_success,
        fallback_used=fallback_used,
        retry_used=retry_used,
        assistant_message=normalized["assistant_message"],
        dashboard_payload=normalized["dashboard_payload"],
        **response_kwargs,
    )
'''

new_text = text[:start] + new_function + text[end:]
path.write_text(new_text, encoding="utf-8")

print("generate_travel_response replaced successfully")