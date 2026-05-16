# --- API для старых датчиков (GET) ---
@router.get("/measurement", response_class=PlainTextResponse)
async def receive_measurement(request: Request):
    """
    Обработка старых GET-запросов вида /505?temp=25.5
    """
    # Игнорируем запрос фавиконки из браузера

    query_params = request.query_params
    location = 'test'

    # Обработка параметров (например, ?temp=25.5)
    for measurement, value in query_params.items():
        try:
            val_float = float(value)
            # Формируем кортеж, как в старом коде
            data = (location, measurement, val_float)
            db.saveMeasurement(data)
        except ValueError:
            logging.error(f"Invalid value for {measurement}: {value}")

    return f"GET request for /{location} processed"