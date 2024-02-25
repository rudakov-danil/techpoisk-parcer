mb = {
       "author": None,
       "chipset": None,
       "socket": None,
       "memory_type": None,
       "memory_type_amount": None,
       "form_factor": None,
       "m2_amount": None,}

cpu = {
    "author": None,
    "line": None,
    "model": None,
    "delivery_type": None,
    "socket": None, 
    "core_number": None,
    "threads_number": None,
    "clock_frequency": None,
    "boost_clock_frequency": None,
    "tdp": None,
    "tech_process": None,
    "integrated_video_core": None,
}


gpu = {
    "author": None,
    "model": None,
    "video_card_author": None,
    "memory_amount": None,
    "interface": None,
    "clock_frequency": None,
    "memory_type" :None,
    "memory_frequency": None,
}

ram = {
    "author": None,
    "memory_amount": None,
    "memory_type": None,
    "memory_frequency": None,
    "is_kit": None,
    "memory_speed": None,
    "timings": None,
    "is_XMP": None,
}

ssd = {
    "author": None,
    "purpose": None,
    "type": None,
    "ssd_drive_capacity": None,
    "form_factor": None,
    "interface": None,
    "nvme_support": None,
    "reading_speed": None,
    "writing_speed": None,
}

hdd = {
    "author": None,
    "hard_disk_capacity": None,
    "purpose": None,
    "type": None,
    "form_factor": None,
    "interface": None,
    "rotational_speed": None,
}

spu = {
    "author": None,
    "power": None,
    "form_factor": None,
    "fan_size": None,
    "certificate": None,
}

pc_case = {
    "author": None,
    "typesize": None,
    "form_factor": None,
    "has_power_unit": None,
    "is_window": None,
    "power_unit_position": None,
    "max_gpu_length": None,
    "max_cpu_height": None,
}

cool_cpu = {
    "author": None,
    "model": None,
    "socket": None,
    "fan_size": None,
    "fan_speed": None,
    "tdp": None,
}
cool_lck = {
    "author": None,
    "model": None,
    "type_cooling": None,
    "socket": None,
    "fan_size": None,
    "fan_speed": None,
}

cool_case = {
    "author": None,
    "model": None,
    "fan_size": None,
    "fan_speed": None,
}

class descriptor():
    
    category = dict()
    def __init__(self,cat_name):
        match cat_name:
            case 'cpu':
                self.category = cpu
            case 'mb':
                self.category = mb
            case 'ram':
                self.category = ram
            case 'gpu':
                self.category = gpu
            case 'ssd':
                self.category = ssd
            case 'hdd':
                self.category = hdd
            case 'spu':
                self.category = spu
            case 'pc_case':
                self.category = pc_case
            case 'cool_cpu':
                self.category = cool_cpu
            case 'cool_lck':
                self.category = cool_lck
            case 'cool_case':
                self.category = cool_case



def checker(info:dict):
    missing_info = []
    for tab in info.keys():
        if info[tab] is None:
            missing_info.append(tab)
    return missing_info

