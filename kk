## Fetching Main-Record
@router.get(
    "/",
    response_model=MainListResponse,
    summary="Get all main records",
    description="Retrieve all active main records with optional filtering"
)
async def get_main_records(
    keycloak_user: Annotated[UserInSignInKeyCloak, Depends(get_user_info)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    skip: int = 0,
    limit: int = 100,
    status_filter: AccountStatus | None = None,
    gazetteer_code: str | None = None,
):
    # Validate user
    await validate_user(keycloak_user.username, keycloak_user, db)
    
    try:
        if status_filter:
            records = await crud_main.get_by_status(db=db, status=status_filter, skip=skip, limit=limit)
        elif gazetteer_code:
            records = await crud_main.get_by_gazetteer_code(db=db, gazetteer_code=gazetteer_code, skip=skip, limit=limit)
        else:
            records = await crud_main.get_all_active(db=db, skip=skip, limit=limit)
        
        result = []
        for record in records:
            # Attach asset URLs
            asset_urls = await attach_asset_urls(db, record.id, keycloak_user.token)

            try:
                score_question_parsed = json.loads(record.score_question) if record.score_question else []
            except json.JSONDecodeError:
                score_question_parsed = []

            

            record_dict = MainRead(
                id=record.id,
                phone_number=record.phone_number,
                gender=record.gender,
                dob=record.dob,
                # have_eq_card=record.have_eq_card,
                eq_card=record.eq_card,
                disability_date=record.disability_date,
                gazetteer_code=record.gazetteer_code,
                status=record.status,
                notes=record.notes,
                spid=record.spid,
                latitude=record.latitude,
                longitude=record.longitude,
                remarks=record.remarks,
                created_by=record.created_by,
                updated_by=record.updated_by,
                disability_code=record.disability_code,
                family_name=record.family_name,
                given_name=record.given_name,
                family_name_en=record.family_name_en,
                given_name_en=record.given_name_en,
                disability_photo=asset_urls.get("disability_photo"),
                disability_photo_infor=asset_urls.get("disability_photo_infor"),
                idpoor_status=record.idpoor_status,
                vacine_status=record.vacine_status,
                vacine_date=record.vacine_date,
                live_with_who=record.live_with_who,
                reason_disability=record.reason_disability,
                year_start_disability=record.year_start_disability,
                submit_date=record.submit_date,
                child_education_level=record.child_education_level,
                is_educated=record.is_educated,
                education_level=record.education_level,
                have_income=record.have_income,
                primary_job=record.primary_job,
                find_job=record.find_job,
                no_job_reason=record.no_job_reason,
                no_job_reason_other=record.no_job_reason_other,
                no_tvet=record.no_tvet_reason,
                is_tvet=record.is_tvet,
                daily_help=record.daily_help,
                chronic_diseases=record.chronic_diseases,
                score_status_live=record.score_status_live,
            )

            result.append(record_dict)
    
        return {
            "error": False,
            "message": "Successful fetching main records",
            "data": result
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to fetch main records: {str(e)}",
            "data": []
        }


==============================


## Fetching Detail Main-Record
@router.get(
    "/{main_record_id}",
    response_model=MainRecordResponse,
    summary="Get main record by ID",
)
async def get_main_record(
    main_record_id: int,
    keycloak_user: Annotated[UserInSignInKeyCloak, Depends(get_user_info)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    # Step 1: Validate user access
    await validate_user(keycloak_user.username, keycloak_user, db)

    try:
        # Step 2: Fetch the main record from DB
        record = await crud_main.get(db=db, id=main_record_id)

        if not record or record.get("is_deleted"):
            return MainRecordResponse(
                error=True,
                message=f"Main record with ID {main_record_id} not found",
                data=None
            )

        # === FIX: Parse score_question from JSON string to list ===
        score_question_str = record.get("score_question")
        try:
            parsed_score_question = json.loads(score_question_str) if score_question_str else []
        except json.JSONDecodeError:
            parsed_score_question = []  # fallback to empty list if corrupted

        # Override the string with the actual list
        record["score_question"] = parsed_score_question

        # Step 3: Now safely convert to Pydantic model
        main_read = MainRead(**record)

        # Step 4: Attach MinIO asset URLs
        asset_urls = await attach_asset_urls(db, main_record_id, keycloak_user.token)
        
        main_read.disability_photo_path = asset_urls.get("disability_photo")
        main_read.disability_photo_infor_path = asset_urls.get("disability_photo_infor")
        main_read.disability_photo_doc_path = asset_urls.get("disability_photo_doc")

        # Optional: add other common asset paths if needed
        # e.g., main_read.family_book_path = asset_urls.get("family_book")

        # Step 5: Return successful response
        return MainRecordResponse(
            error=False,
            message="Successful for fetching detail main record",
            data=main_read
        )

    except Exception as e:
        logging.error(f"Error fetching main record {main_record_id}: {str(e)}", exc_info=True)
        
        # Only expose detailed error in non-production
        error_msg = str(e)
        if settings.ENVIRONMENT == "production":
            error_msg = "Internal server error"

        return MainRecordResponse(
            error=True,
            message=f"Fail for fetching detail main record: {error_msg}",
            data=None
        )



=========================
{
	"error": false,
	"message": "Successful fetching main records",
	"data": [
		{
			"phone_number": null,
			"gender": "FEMALE",
			"dob": "2018-06-21",
			"eq_card": null,
			"disability_date": "2019-01-01",
			"gazetteer_code": "02020306",
			"family_name": "មា",
			"given_name": "ប៉",
			"family_name_en": "Van",
			"given_name_en": "Bro",
			"disability_code": "020203060822352",
			"disability_photo": "https://spr-stgapi.digitalsp.gov.kh/api/v1/Files/portal-pwd-dev/201/main/disability_photo_8642b3d0-120d-49e2-90fd-903dd0c1a090.png?token=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJJcHN2bFg2Y081NFRycmRFWk95NlJ0VlBld0UwWFItUkpXMVd3Z1ZCNmI4In0.eyJleHAiOjE3Njk2NTg1ODQsImlhdCI6MTc2OTA1Mzc4NCwianRpIjoiMjVhY2Q5MzEtMTkxMi00ODM2LTk2OGItYTJlZjdlMTk2ZWMzIiwiaXNzIjoiaHR0cHM6Ly9pZG0uZGlnaXRhbHNwLmdvdi5raC9yZWFsbXMvcG9ydGFsLW1vbm9yZXBvIiwiYXVkIjpbInBvcnRhbC1wd2QiLCJhY2NvdW50IiwicG9ydGFsLWlkcG9vciJdLCJzdWIiOiJiZDM0Yjk2Zi01MDJhLTQ1ZjUtOWMzYy05OGQwNzA3ODI2ZTEiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwb3J0YWwtbW9ub3JlcG8iLCJzZXNzaW9uX3N0YXRlIjoiY2U2ZmVlY2YtMDE2Yi00N2EyLWFhZjgtMjI5ZWE5MGE2NjI2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL3N0YWdpbmcuZGlnaXRhbHNwLmdvdi5raC8qIiwiaHR0cDovL2xvY2FsaG9zdDozMDAwMC8qIiwiaHR0cDovL2xvY2FsaG9zdDozMDAwLyoiLCJodHRwczovL2FkbWluLmRpZ2l0YWxzcC5nb3Yua2gvKiIsImh0dHA6Ly9sb2NhbGhvc3QvKiIsImh0dHBzOi8vZGV2LmRpZ2l0YWxzcC5nb3Yua2gvKiJdLCJyZXNvdXJjZV9hY2Nlc3MiOnsicG9ydGFsLW1vbm9yZXBvIjp7InJvbGVzIjpbImNhIiwib3BlcmF0b3IiXX0sInBvcnRhbC1wd2QiOnsicm9sZXMiOlsiY2EiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfSwicG9ydGFsLWlkcG9vciI6eyJyb2xlcyI6WyJjYSJdfX0sInNjb3BlIjoiZW1haWwgcHJvZmlsZSIsInNpZCI6ImNlNmZlZWNmLTAxNmItNDdhMi1hYWY4LTIyOWVhOTBhNjYyNiIsIm5zYWZfcGFzc3dvcmQiOiJnQUFBQUFCbjY4dk5acFJSTVJDZ1g3aTFOaEJ3c1lWajdsNlBfMnozN1c3a2V5VUpHcS14YlIyM3ZwaFUzOUZwa2Z0ZWlyc1A4dDI1WWFYWDFTREpkTU92WUJIbUdYV00wZz09IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImNvbW11bmVfbmFtZSI6IuGen-GehOGfkuGegOGetuGej-Gfi-Gen-GetuGem-GetuGegOGfhuGemuGevuGegCIsInByZWZlcnJlZF91c2VybmFtZSI6InZlYXNuYV9jYSIsImdpdmVuX25hbWUiOiLhnpjhnpPhn5Lhno_hn5LhnprhnrjhnqLhnpPhnrvhnpzhno_hn5Lhno_hnoDhnpjhn5LhnpjhnpzhnrfhnpLhnrgiLCJwcm92aW5jZV9uYW1lIjoiQmFudGVheSBNZWFuY2hleSIsImNsaWVudF9yb2xlcyI6WyJjYSIsIm9wZXJhdG9yIiwiY2EiLCJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIiwiY2EiXSwiZ2F6ZXR0ZWVyX2NvZGUiOiIxNzEwMDQiLCJuc2FmX3VzZXJuYW1lIjoidmVhc25hX2NhIiwibmFtZSI6IuGemOGek-GfkuGej-GfkuGemuGeuOGeouGek-Geu-GenOGej-GfkuGej-GegOGemOGfkuGemOGenOGet-GekuGeuCIsInB3ZF91c2VybmFtZSI6ImdzX2NvbW11bmUiLCJlbWFpbCI6InZlYXNuYV9jYUBnbWFpbC5jb20iLCJ1c2VybmFtZSI6InZlYXNuYV9jYSJ9.paaGgdMlXQGUJ_gmGf96Kv2Ojp-jR9B_GN62Em3lPTY-heD1iCE_NgCOvijY4MwDQIp5Syn83VPuKG27YQYMKzZ7zs-MOpMJsU6Iofkcy5wX96Nv9gcZ4TbM7R6lT8TorVVrS3X8BdHolVPp0PyHHtBRuhXqsBqT79FHJnyh4hLpU1YIfeSN1hX7M2CE2xiZGaMf0ZtvkjIondximTXiHAnoiJm2dc1oIhQgUguWW-CAxYoXqO-bl1wgb-U7LXhl_-R0UzBJ5bUaFemX3FBuzDcaMBnxHNjzKXVqx43jma5b6dLLfgmA4nnhnZ1PElzQgHudknusbjHvVtGReSHe1g",
			"disability_photo_infor": "https://spr-stgapi.digitalsp.gov.kh/api/v1/Files/portal-pwd-dev/201/main/disability_photo_full_e2ead854-10e1-48f1-962f-3b73b921091f.png?token=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJJcHN2bFg2Y081NFRycmRFWk95NlJ0VlBld0UwWFItUkpXMVd3Z1ZCNmI4In0.eyJleHAiOjE3Njk2NTg1ODQsImlhdCI6MTc2OTA1Mzc4NCwianRpIjoiMjVhY2Q5MzEtMTkxMi00ODM2LTk2OGItYTJlZjdlMTk2ZWMzIiwiaXNzIjoiaHR0cHM6Ly9pZG0uZGlnaXRhbHNwLmdvdi5raC9yZWFsbXMvcG9ydGFsLW1vbm9yZXBvIiwiYXVkIjpbInBvcnRhbC1wd2QiLCJhY2NvdW50IiwicG9ydGFsLWlkcG9vciJdLCJzdWIiOiJiZDM0Yjk2Zi01MDJhLTQ1ZjUtOWMzYy05OGQwNzA3ODI2ZTEiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwb3J0YWwtbW9ub3JlcG8iLCJzZXNzaW9uX3N0YXRlIjoiY2U2ZmVlY2YtMDE2Yi00N2EyLWFhZjgtMjI5ZWE5MGE2NjI2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL3N0YWdpbmcuZGlnaXRhbHNwLmdvdi5raC8qIiwiaHR0cDovL2xvY2FsaG9zdDozMDAwMC8qIiwiaHR0cDovL2xvY2FsaG9zdDozMDAwLyoiLCJodHRwczovL2FkbWluLmRpZ2l0YWxzcC5nb3Yua2gvKiIsImh0dHA6Ly9sb2NhbGhvc3QvKiIsImh0dHBzOi8vZGV2LmRpZ2l0YWxzcC5nb3Yua2gvKiJdLCJyZXNvdXJjZV9hY2Nlc3MiOnsicG9ydGFsLW1vbm9yZXBvIjp7InJvbGVzIjpbImNhIiwib3BlcmF0b3IiXX0sInBvcnRhbC1wd2QiOnsicm9sZXMiOlsiY2EiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfSwicG9ydGFsLWlkcG9vciI6eyJyb2xlcyI6WyJjYSJdfX0sInNjb3BlIjoiZW1haWwgcHJvZmlsZSIsInNpZCI6ImNlNmZlZWNmLTAxNmItNDdhMi1hYWY4LTIyOWVhOTBhNjYyNiIsIm5zYWZfcGFzc3dvcmQiOiJnQUFBQUFCbjY4dk5acFJSTVJDZ1g3aTFOaEJ3c1lWajdsNlBfMnozN1c3a2V5VUpHcS14YlIyM3ZwaFUzOUZwa2Z0ZWlyc1A4dDI1WWFYWDFTREpkTU92WUJIbUdYV00wZz09IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImNvbW11bmVfbmFtZSI6IuGen-GehOGfkuGegOGetuGej-Gfi-Gen-GetuGem-GetuGegOGfhuGemuGevuGegCIsInByZWZlcnJlZF91c2VybmFtZSI6InZlYXNuYV9jYSIsImdpdmVuX25hbWUiOiLhnpjhnpPhn5Lhno_hn5LhnprhnrjhnqLhnpPhnrvhnpzhno_hn5Lhno_hnoDhnpjhn5LhnpjhnpzhnrfhnpLhnrgiLCJwcm92aW5jZV9uYW1lIjoiQmFudGVheSBNZWFuY2hleSIsImNsaWVudF9yb2xlcyI6WyJjYSIsIm9wZXJhdG9yIiwiY2EiLCJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIiwiY2EiXSwiZ2F6ZXR0ZWVyX2NvZGUiOiIxNzEwMDQiLCJuc2FmX3VzZXJuYW1lIjoidmVhc25hX2NhIiwibmFtZSI6IuGemOGek-GfkuGej-GfkuGemuGeuOGeouGek-Geu-GenOGej-GfkuGej-GegOGemOGfkuGemOGenOGet-GekuGeuCIsInB3ZF91c2VybmFtZSI6ImdzX2NvbW11bmUiLCJlbWFpbCI6InZlYXNuYV9jYUBnbWFpbC5jb20iLCJ1c2VybmFtZSI6InZlYXNuYV9jYSJ9.paaGgdMlXQGUJ_gmGf96Kv2Ojp-jR9B_GN62Em3lPTY-heD1iCE_NgCOvijY4MwDQIp5Syn83VPuKG27YQYMKzZ7zs-MOpMJsU6Iofkcy5wX96Nv9gcZ4TbM7R6lT8TorVVrS3X8BdHolVPp0PyHHtBRuhXqsBqT79FHJnyh4hLpU1YIfeSN1hX7M2CE2xiZGaMf0ZtvkjIondximTXiHAnoiJm2dc1oIhQgUguWW-CAxYoXqO-bl1wgb-U7LXhl_-R0UzBJ5bUaFemX3FBuzDcaMBnxHNjzKXVqx43jma5b6dLLfgmA4nnhnZ1PElzQgHudknusbjHvVtGReSHe1g",
			"disability_photo_doc": null,
			"id": 201,
			"status": "CA_D",
			"notes": null,
			"spid": null,
			"latitude": null,
			"longitude": null,
			"remarks": null,
			"created_by": 1,
			"updated_by": null,
			"idpoor_status": null,
			"vacine_status": "None",
			"vacine_date": null,
			"live_with_who": "ឪពុកម្តាយ",
			"reason_disability": "ជំងឺ",
			"year_start_disability": "2019",
			"submit_date": "2024-04-25",
			"child_education_level": null,
			"is_educated": "ឈប់រៀន",
			"education_level": null,
			"have_income": null,
			"primary_job": null,
			"find_job": null,
			"no_job_reason": null,
			"no_job_reason_other": null,
			"no_tvet": null,
			"is_tvet": null,
			"daily_help": null,
			"chronic_diseases": null,
			"score_status_live": null,
			"score_question": []
		},


===============================
======================

    async def get_full_by_main(
        self,
        db: AsyncSession,
        main_id: int
    ):
        # Alias disability_type table
        MainCategory = aliased(DisabilityType)
        SubCategory = aliased(DisabilityType)

        stmt = (
            select(
                # Main category (parent)
                MainCategory.code.label("main_category_code"),
                MainCategory.title.label("main_category_title"),

                # Sub category (child)
                SubCategory.code.label("sub_category_code"),
                SubCategory.title.label("sub_category_title"),

                # Question & Answer
                Question.question.label("question_title"),
                Answer.answer.label("answer_title"),
            )
            .select_from(QuestionAnswer)

            # Join question & answer
            .join(
                Question,
                Question.unique_code == QuestionAnswer.question_code
            )
            .join(
                Answer,
                Answer.unique_code == QuestionAnswer.answer_code
            )

            # Join sub category
            .join(
                SubCategory,
                SubCategory.code == QuestionAnswer.category_code
            )

            # Join main category (parent of sub category)
            .join(
                MainCategory,
                MainCategory.code == SubCategory.parent_code
            )

            .where(
                QuestionAnswer.main_id == main_id,
                QuestionAnswer.is_deleted.is_(False),
            )
        )

        result = await db.execute(stmt)

        # Convert rows to list of dict
        return [
            {
                "main_category_code": row.main_category_code,
                "main_category_title": row.main_category_title,
                "sub_category_code": row.sub_category_code,
                "sub_category_title": row.sub_category_title,
                "question_title": row.question_title,
                "answer_title": row.answer_title,
            }
            for row in result.all()
        ]
