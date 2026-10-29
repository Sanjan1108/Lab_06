import pytest
from ski_resort_pass import (
    process_resort_bookings,
    check_chairlift_anemometer,
)


# ==========================================
# BOOKING PROCESSING TESTS
# ==========================================

def test_single_adult_full_day():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "includes_lodge_locker": False,
        "skiers": [
            {"age": 30, "gear_rental": False, "blackout_override": False}
        ],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 80.0, "status": "COMPLETED"}


def test_invalid_groups_type():
    with pytest.raises(ValueError):
        process_resort_bookings("invalid", 15.0)


def test_negative_facility_fee():
    with pytest.raises(ValueError):
        process_resort_bookings([], -1.0)


def test_empty_groups():
    result = process_resort_bookings([], 15.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_inactive_group_is_skipped():
    groups = [{
        "is_active": False,
        "duration": "full_day",
        "skiers": [{"age": 30}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["status"] == "ZERO_SALES"


def test_default_group_values():
    groups = [{"is_active": True}]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


@pytest.mark.parametrize(
    "duration, expected_rate",
    [
        ("season", 300.0),
        ("full_day", 80.0),
        ("half_day", 50.0),
    ],
)
def test_valid_pass_durations(duration, expected_rate):
    groups = [{
        "is_active": True,
        "duration": duration,
        "skiers": [{"age": 30}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == expected_rate
    assert result["status"] == "COMPLETED"


def test_invalid_duration():
    groups = [{
        "is_active": True,
        "duration": "weekly",
        "skiers": [{"age": 30}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_child_discount():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 10}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 48.0


def test_child_age_boundary():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 11}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 48.0


def test_adult_age_boundary():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 12}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 80.0


def test_regular_adult_price():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 30}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 80.0


def test_senior_discount():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 65}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 56.0


def test_age_below_one_is_rejected():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 0}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_gear_rental():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 30, "gear_rental": True}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 115.0


def test_lodge_locker_fee():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "includes_lodge_locker": True,
        "skiers": [{"age": 30}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 95.0


def test_blackout_override_regular_pass():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 30, "blackout_override": True}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 40.0


def test_blackout_override_half_day():
    groups = [{
        "is_active": True,
        "duration": "half_day",
        "skiers": [
            {"age": 30, "blackout_override": True},
            {"age": 30},
        ],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_audit_review_after_more_than_four_rejections():
    groups = [
        {"is_active": True, "duration": "weekly", "skiers": []}
        for _ in range(5)
    ]
    result = process_resort_bookings(groups, 15.0)
    assert result["status"] == "AUDIT_REVIEW"


def test_exactly_four_rejections():
    groups = [
        {"is_active": True, "duration": "weekly", "skiers": []}
        for _ in range(4)
    ]
    result = process_resort_bookings(groups, 15.0)
    assert result["status"] == "ZERO_SALES"


def test_multiple_skiers():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 10}, {"age": 30}, {"age": 65}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 184.0


def test_invalid_age_then_valid_skier():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 0}, {"age": 30}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["total_revenue"] == 80.0


def test_invalid_age_with_blackout_override():
    groups = [{
        "is_active": True,
        "duration": "full_day",
        "skiers": [{"age": 0, "blackout_override": True}],
    }]
    result = process_resort_bookings(groups, 15.0)
    assert result["status"] == "ZERO_SALES"


# ==========================================
# CHAIRLIFT ANEMOMETER TESTS
# ==========================================

def test_no_wind_data():
    assert check_chairlift_anemometer([]) == "NO_DATA"


def test_safe_wind_speeds():
    assert check_chairlift_anemometer([[20, 30, 40]]) == "SAFE_OPERATION"


def test_single_high_gust():
    assert check_chairlift_anemometer([[50, 30]]) == "SAFE_OPERATION"


def test_two_consecutive_high_gusts():
    assert check_chairlift_anemometer([[50, 51]]) == "SUSPEND_LIFT"


def test_high_gusts_separated_by_safe_speed():
    assert check_chairlift_anemometer([[50, 30, 51]]) == "SAFE_OPERATION"


def test_consecutive_high_gusts_in_second_lift():
    assert check_chairlift_anemometer([[50], [46, 47]]) == "SUSPEND_LIFT"


def test_wind_speed_exactly_45():
    assert check_chairlift_anemometer([[45, 45]]) == "SAFE_OPERATION"


def test_empty_lift_readings():
    assert check_chairlift_anemometer([[], [20, 30]]) == "SAFE_OPERATION"

