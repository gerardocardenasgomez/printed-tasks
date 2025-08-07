import configparser

def get_config(full_path: str):
    config = configparser.ConfigParser()
    config.read(full_path)
    return config

def printer_word_wrap(message: str) -> str:
    MAX_CHARS_PER_LINE =  48
    wrapped_message = []
    line_start_idx = 0

    while line_start_idx < len(message):
        line_end_idx_candidate = min(line_start_idx + MAX_CHARS_PER_LINE, len(message))

        newline_idx = message.find('\n', line_start_idx, line_end_idx_candidate)
        if newline_idx != -1:
            wrapped_message.append(message[line_start_idx:newline_idx])
            line_start_idx = newline_idx + 1
            continue

        # This never execs if newlines are found
        break_point_idx = -1
        for i in range(line_end_idx_candidate - 1, line_start_idx - 1, -1):
            if message[i] == ' ':
                break_point_idx = i
                break

        if break_point_idx != -1 and break_point_idx >= line_start_idx:
            # found somewhere to break hehe
            current_line = message[line_start_idx:break_point_idx]
            next_line_start_offset = break_point_idx + 1
        else:
            current_line =  message[line_start_idx:line_end_idx_candidate]
            next_line_start_offset = line_end_idx_candidate

        wrapped_message.append(current_line.strip())
        line_start_idx = next_line_start_offset

        while line_start_idx < len(message) and message[line_start_idx] == ' ':
            line_start_idx += 1

    return "\n".join(wrapped_message)

def get_barcode(task_id: str) -> str:
    encoded_task_id = task_id.encode("ascii")
    cmd = b''
    # Set HRI (Human Readable Interpretation) 
    cmd += b'\x1d\x48\x02'  # HRI below barcode
    # Barcode height
    cmd += b'\x1d\x68\x50'  # 80 dots height
    # Barcode width  
    cmd += b'\x1d\x77\x02'  # Width multiplier 2
    # CODE128 command
    cmd += b'\x1d\x6b\x49'  # Select CODE128
    # Length: original data + 2 bytes for {B prefix
    cmd += bytes([len(encoded_task_id) + 2])
    # CODE128 subset B selection (for alphanumeric)
    cmd += b'{B'  
    # Your actual data
    cmd += encoded_task_id
    # Line feed to finish
    cmd += b'\x0a'
    
    # Convert to hex string for transmission
    return 'hex:' + cmd.hex()