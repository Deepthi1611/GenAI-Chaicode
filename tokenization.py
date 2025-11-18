import tiktoken

encoder = tiktoken.encoding_for_model("gpt-4o")

# vocab size for gpt-4 - vocab size is the total number of unique tokens for the model
print("vocab size:", encoder.n_vocab)

# input query
text = 'the cat sat on the mat'
# tokenization
tokens = encoder.encode(text)
print("tokens:", tokens) # tokens are same every time for same input

# decoding / detokenization
my_tokens = [3086, 9059, 10139, 402, 290, 2450]
decoded_text = encoder.decode(my_tokens)
print("decoded text:", decoded_text) # decoded text is same every time for same tokens