import { useEffect, useRef } from 'react';

const ParticleBackground = () => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let animationFrameId;
        let particles = [];
        let mouse = { x: null, y: null, radius: 150 };

        // Particle class
        class Particle {
            constructor() {
                this.reset();
                this.y = Math.random() * canvas.height;
                this.opacity = Math.random() * 0.5 + 0.3;
            }

            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 3 + 1;
                this.baseSpeedX = (Math.random() - 0.5) * 0.6;
                this.baseSpeedY = (Math.random() - 0.5) * 0.6;
                this.speedX = this.baseSpeedX;
                this.speedY = this.baseSpeedY;
                // More red particles for emphasis
                this.color = Math.random() > 0.35 ? '#dc2626' : '#ffffff';
                this.pulsePhase = Math.random() * Math.PI * 2;
            }

            update() {
                // Mouse interaction
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < mouse.radius && mouse.x !== null) {
                    const force = (mouse.radius - distance) / mouse.radius;
                    const angle = Math.atan2(dy, dx);
                    this.speedX = this.baseSpeedX - Math.cos(angle) * force * 2;
                    this.speedY = this.baseSpeedY - Math.sin(angle) * force * 2;
                } else {
                    this.speedX += (this.baseSpeedX - this.speedX) * 0.05;
                    this.speedY += (this.baseSpeedY - this.speedY) * 0.05;
                }

                this.x += this.speedX;
                this.y += this.speedY;

                // Wrap around screen
                if (this.x > canvas.width) this.x = 0;
                if (this.x < 0) this.x = canvas.width;
                if (this.y > canvas.height) this.y = 0;
                if (this.y < 0) this.y = canvas.height;

                // Update pulse
                this.pulsePhase += 0.02;
            }

            draw() {
                const pulse = Math.sin(this.pulsePhase) * 0.3 + 0.7;
                const currentSize = this.size * pulse;

                // Glow effect
                const gradient = ctx.createRadialGradient(
                    this.x, this.y, 0,
                    this.x, this.y, currentSize * 3
                );

                if (this.color === '#dc2626') {
                    gradient.addColorStop(0, `rgba(220, 38, 38, ${this.opacity * pulse})`);
                    gradient.addColorStop(0.5, `rgba(220, 38, 38, ${this.opacity * pulse * 0.3})`);
                    gradient.addColorStop(1, 'rgba(220, 38, 38, 0)');
                } else {
                    gradient.addColorStop(0, `rgba(255, 255, 255, ${this.opacity * pulse})`);
                    gradient.addColorStop(0.5, `rgba(255, 255, 255, ${this.opacity * pulse * 0.2})`);
                    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
                }

                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.arc(this.x, this.y, currentSize * 3, 0, Math.PI * 2);
                ctx.fill();

                // Core particle
                ctx.fillStyle = this.color;
                ctx.globalAlpha = this.opacity * pulse;
                ctx.beginPath();
                ctx.arc(this.x, this.y, currentSize, 0, Math.PI * 2);
                ctx.fill();
                ctx.globalAlpha = 1;
            }
        }

        // Initialize particles
        const initParticles = () => {
            particles = [];
            const particleCount = Math.min(Math.floor((canvas.width * canvas.height) / 12000), 120);
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle());
            }
        };

        // Set canvas size
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initParticles();
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Mouse move handler
        const handleMouseMove = (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        };
        window.addEventListener('mousemove', handleMouseMove);


        // Draw connections between nearby particles
        const drawConnections = () => {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < 140) {
                        const opacity = (1 - distance / 140) * 0.2;

                        // Red connections for red particles
                        if (particles[i].color === '#dc2626' && particles[j].color === '#dc2626') {
                            ctx.strokeStyle = `rgba(220, 38, 38, ${opacity})`;
                        } else {
                            ctx.strokeStyle = `rgba(255, 255, 255, ${opacity * 0.5})`;
                        }

                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }
        };

        // Animation loop
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw connections first (behind particles)
            drawConnections();

            // Update and draw particles
            particles.forEach(particle => {
                particle.update();
                particle.draw();
            });

            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        // Cleanup
        return () => {
            window.removeEventListener('resize', resizeCanvas);
            window.removeEventListener('mousemove', handleMouseMove);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="particle-canvas"
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                zIndex: 1
            }}
        />
    );
};

export default ParticleBackground;
