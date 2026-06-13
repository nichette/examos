#!/bin/bash
# Name: auto-install.sh
# Purpose: Automatically format the drive and install the Exam OS offline.

echo "Starting Automated Exam OS Installation..."

# 1. Smartly detect the target drive
if [ -b "/dev/nvme0n1" ]; then
    # Modern NVMe Drive
    DRIVE="/dev/nvme0n1"
    PART1="${DRIVE}p1"
    PART2="${DRIVE}p2"
elif [ -b "/dev/vda" ]; then
    # Virtual Machine Drive (VirtIO)
    DRIVE="/dev/vda"
    PART1="${DRIVE}1"
    PART2="${DRIVE}2"
elif [ -b "/dev/sda" ]; then
    # Standard SATA/USB Drive
    DRIVE="/dev/sda"
    PART1="${DRIVE}1"
    PART2="${DRIVE}2"
else
    echo "Error: Could not find a suitable hard drive (checked nvme0n1, vda, sda)!"
    exit 1
fi

echo "Found target drive at $DRIVE"

# 2. Wipe the drive completely
echo "Wiping drive..."
wipefs -a $DRIVE

# 3. Create partitions (1=EFI boot 512MB, 2=Root)
echo "Partitioning drive..."
parted -s $DRIVE mklabel gpt
parted -s $DRIVE mkpart ESP fat32 1MiB 513MiB
parted -s $DRIVE set 1 esp on
parted -s $DRIVE mkpart primary ext4 513MiB 100%

# 4. Format the partitions
echo "Formatting partitions..."
mkfs.fat -F32 $PART1
mkfs.ext4 -F $PART2

# 5. Mount the partitions to prepare for installation
mount $PART2 /mnt
mkdir -p /mnt/boot
mount $PART1 /mnt/boot

# 6. Point the installer to our Offline Backpack instead of the internet
cat <<EOF > /tmp/custom-pacman.conf
[options]
Architecture = auto
[exam-repo]
SigLevel = Optional TrustAll
Server = file:///offline-repo
EOF

# 7. Unpack the backpack! 
echo "Installing base system..."
pacstrap -C /tmp/custom-pacman.conf /mnt base linux linux-firmware amd-ucode intel-ucode cage xorg-xwayland python python-gobject gtk4 gnupg rsync grub efibootmgr

# Move the custom Python Exam App into the new System
echo "Copying Exam Application..."
cp -r /opt/exam-app /mnt/opt
# --- NEW: Set up Auto-Login for the student on the new hard drive ---
echo "Configuring automatic login..."
mkdir -p /mnt/etc/systemd/system/getty@tty1.service.d
cat << 'CONFIG' > /mnt/etc/systemd/system/getty@tty1.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin exam-kiosk --noclear %I $TERM
CONFIG

# --- NEW: Set up Auto-Start for Cage and the Python App ---
echo "Configuring graphical kiosk auto-start..."
mkdir -p /mnt/etc/skel
cat << 'CONFIG' > /mnt/etc/skel/.bash_profile
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec cage -- /opt/exam-app/main.py
fi
CONFIG

# 8. Generate the file system table
genfstab -U /mnt >> /mnt/etc/fstab

# 9. Enter the new system to set up the bootloader and the student user
echo "Setting up bootloader and users..."
arch-chroot /mnt /bin/bash <<EOF

# Install the GRUB Bootloader
grub-install --target=x86_64-efi --efi-directory=/boot --removable
grub-mkconfig -o /boot/grub/grub.cfg

# Create the single, restricted system user for the exam
useradd -m -G input,video -s /bin/bash exam-kiosk

# Give it a basic system password (we will set it to auto-login later)
echo "exam-kiosk:systempass" | chpasswd

EOF

echo "Installation Complete! Rebooting in 5 seconds..."
sleep 5
reboot
