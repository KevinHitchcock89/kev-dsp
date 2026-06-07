#staticmethod
class utils():    
    def to_bits(data):
        """
        Convert int, binary string, or bit string into a list of bits [0,1]
        """
        # Case 1: integer
        if isinstance(data, int):
            return [int(b) for b in bin(data)[2:]]

        # Case 2: string
        if isinstance(data, str):
            data = data.strip()

            # Handle "0b101"
            if data.startswith("0b"):
                data = data[2:]

            # Validate it's binary
            if not all(c in "01" for c in data):
                raise ValueError("String must contain only 0 or 1")

            return [int(b) for b in data]

        # Case 3: already list of bits
        if isinstance(data, list):
            if not all(b in [0, 1] for b in data):
                raise ValueError("List must contain only 0 or 1")
            return data

        raise TypeError("Unsupported data type")  

    def replace_value( arr, old, new):
        return [new if x == old else x for x in arr]

    def int_to_bits(value, width):
        return [int(b) for b in format(value, f'0{width}b')]

    def text_to_bits(msg):
        if not isinstance(msg,str):
            raise ValueError("Message must be a string")
        
        return ''.join(f"{ord(c):08b}" for c in msg)