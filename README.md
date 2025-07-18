# zsh-wrapped
### *spotify wrapped for nerds*
____
This is a program that gives various stats about your terminal history in a visually appealing manner. 

This should work with fish, zsh, bash. (other shells may work too - it will try!)

### installation and running
To install:
```
git clone https://github.com/tillay/zsh-wrapped
cd zsh-wrapped
```
To run:
```
python3 wrapped.py
```

### Notes
____
To have time-based statistics, it needs either the ZSH or FISH shell - other shells do not take timestamps :(

If you have a weird shell, try manually setting the shell variable to your shell if something goes wrong. 

I've been working on an experimental feature to show packages that were installed through the command line. This feature only works on arch-based and debian-based distributions as of now. 

Modify `wrapped.py` to configure the output. I made that file work like a config file so it shouldn't be too hard to those who don't know python. 

The default config file has all the features included, and you can make modifications from there to colors and arguments and such. 

### Images
____
![image](https://github.com/user-attachments/assets/bde42cb9-d345-4849-956c-79d224555e8c)

![image](https://github.com/user-attachments/assets/4bfdffa6-e6da-4241-968b-0b107ba243f0)