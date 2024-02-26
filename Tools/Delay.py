import time

def delaySeconds(seconds):
    time.sleep(seconds)
    
    return None
def delayMicroseconds(microseconds):
    # Xác định thời điểm bắt đầu
    start_time = time.perf_counter_ns()

    # Tính thời điểm kết thúc dự kiến
    end_time = start_time + microseconds * 1000  # Chuyển đổi từ microseconds thành nanoseconds

    # Vòng lặp chờ với độ phân giải 1 nano seconds
    while time.perf_counter_ns() < end_time: pass
    return None